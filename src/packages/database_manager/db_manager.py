import pyodbc
import os
import datetime
from typing import Union

from . import destruct_query_conditions, parse_sql_condition
from packages.log_manager import LogManager

class DatabaseManager:
    def __init__(self, db_path: str, process: str):
        if not db_path:
            raise ValueError("A database file path was not provided to the DatabaseManager.")
        if not os.path.exists(db_path):
            raise ValueError(f"No database exists at the path: {db_path}")
        if not process:
            raise ValueError("A process name is required to initalize a database connection.")
        
        self.db_path = db_path
        self.process = process
        self.connection = None
        self.cursor = None
        
        log_file_dir = os.path.dirname(db_path)
        file_name = os.path.basename(db_path).split('.')[0]
        self.log_manager = LogManager(os.path.join(log_file_dir, f"{file_name}_db_logs.json")).__enter__()
        
    # Only envoked when using "with"(context manager)
    def __enter__(self):
        """Initialize the database connection when entering the context."""
        self.init_db_connection()
        return self
    
    # Only envoked when using "with"(context manager)
    def __exit__(self, exc_type, exc_value, traceback):
        """Close the database connection when exiting the context."""
        if self.connection:
            try:
                self.cursor.close()
                self.connection.close()
            except pyodbc.Error as err:
                raise ConnectionError(f"An error occured while closing the database: {err}")
        # Save logger changes
        self.log_manager.__exit__(exc_type, exc_value, traceback)
        
    def init_db_connection(self):
        """Initialize the database connection."""
        try:
            # Open the connection
            self.connection = pyodbc.connect(
                r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
                r'DBQ=' + self.db_path + ';'
            )
            self.cursor = self.connection.cursor()
        except pyodbc.Error as err:
            raise ConnectionError(f"An error occured while connecting to database: {err}")
        
    # def terminate_db_connection(self):
    #     """Terminate the database connection."""
    #     if self.connection:
    #         try:
    #             self.cursor.close()
    #             self.connection.close()
    #         except pyodbc.Error as err:
    #             raise ConnectionError(f"An error occured while closing the database: {err}")
    #     # Save logger changes
    #     self.log_manager.__exit__()
        
    def get_db_tables(self):
        tables = []
        for row in self.cursor.tables():
            if row.table_type == "TABLE":
                tables.append(row.table_name)
        return tables

    def get_table_columns(self, table: str):
        """Retrieve table column name and type"""
        try:
            query = f"SELECT * FROM {table} WHERE 1=0"
            self.cursor.execute(query)
            # columns = [column[0] for column in self.cursor.description]
            return {column[0]:column[1] for column in self.cursor.description}
        except pyodbc.Error as err:
            print(f"An error occured while querying the database: {err}")
            if self.connection:
                self.connection.rollback()
    
    def select_query(self, table: str, cols: list[Union[str, tuple]] = None, conditions: Union[dict, str] = None, limit: int = None) -> list[dict]:
        """Execute a 'SELECT' query to the database."""
        db_tables = self.get_db_tables()
        if table not in db_tables:
            raise ValueError(f"The table '{table}' does not exist in the database.")

        formatted_limit = f"TOP {limit}" if limit else ""
        formatted_cols = ', '.join([(f"{col[0]} AS {col[1]}" if isinstance(col, tuple) else col) for col in cols]) if cols else '*'
        query = f"SELECT {formatted_limit} {formatted_cols} FROM {table}"
        values = []

        if conditions:
            if (isinstance(conditions, dict)):
                cond_str, cond_vals = self.destruct_query_conditions(conditions)
                values = cond_vals
                query += f" WHERE {cond_str}"
            else:
                query += f" WHERE {conditions}"
            
        # Execute query
        self.cursor.execute(query, values)
        
        rows = self.cursor.fetchall()
        return [dict(zip([column[0] for column in self.cursor.description], row)) for row in rows] if rows else []

    def update_query(self, table: str, cols: dict[str, Union[None, str, int, bool, datetime.date]], conditions: dict = None):
        """Execute an update query"""
        try:
            if table not in self.get_db_tables():
                raise ValueError(f"The table '{table}' does not exist in the database.")
            if not cols:
                raise ValueError("No columns provided for update.")
            
            table_columns = self.get_table_columns(table)
            for col_key, col_prop in cols.items():
                if not col_prop:
                    continue

                col_type = table_columns.get(col_key)
                if not col_type:
                    raise ValueError(f"Table '{table}' does not have column '{col_key}'")
                if not isinstance(col_prop, col_type):
                    cols[col_key] = col_type(col_prop)
                    print(f"Value for column '{col_key}' in table '{table}' was converted from '{type(col_prop)}' to '{col_type}'")
            table_row_identifier = list(table_columns.keys())[0]
            affecting_rows = self.select_query(table, [table_row_identifier, *cols.keys()], conditions)

            if not affecting_rows:
                raise ValueError("Could not find records that satisfied given parameters.")
            
            for row in affecting_rows:
                # changing_fields = {key:val for key, val in cols.items() if (key in row and row[key] != val)}
                changing_properties = [key for key in cols.keys() if (key in row and row[key] != cols[key])]
                if not len(changing_properties):
                    continue

                row_id = row[table_row_identifier]
                formatted_cols = ', '.join([f"{col} = ?" for col in changing_properties])
                query_str = f"UPDATE {table} SET {formatted_cols} WHERE {table_row_identifier} = ?"
                # query_vals = list(changing_fields.values())
                query_vals = [cols[field] for field in changing_properties]

                self.cursor.execute(query_str, [*query_vals, row_id])
                self.log_manager.append_runtime_log(self.process, "update", table, row_id, {prop: row[prop] for prop in changing_properties})
            self.connection.commit()
        except ValueError as err:
            if self.connection:
                self.connection.rollback()
                raise err


    def delete_query(self, table: str, conditions: dict = None):
        try:
            if table not in self.get_db_tables():
                raise ValueError(f"The table '{table}' does not exist in the database.")
            if not conditions:
                raise ValueError("No search conditions provided for deletion.")
            
            table_columns = self.get_table_columns(table)
            record_identifier = list(table_columns.keys())[0]

            affecting_rows = self.select_query(table=table, conditions=conditions)
            if not affecting_rows:
                raise ValueError(f"No records found in '{table}' matching conditions: {conditions}")
            
            for row in affecting_rows:
                record_id = row[record_identifier]
                properties = {k: v for k, v in row.items() if k != record_identifier}

                query_str = f"DELETE FROM {table} WHERE {record_identifier} = ?"
                self.cursor.execute(query_str, [record_id])
                self.log_manager.append_runtime_log(self.process, "delete", table, record_id, properties)
            self.connection.commit()
        except Exception as err:
            if self.connection:
                try:
                    self.connection.rollback()
                except Exception as rollback_err:
                    print("Rollback failed:", rollback_err)
            raise err
                
   # ** Caution: Deprecated
    def execute_query_legacy(self, query, *args):
        """Execute a given SQL query."""
        try:
            self.cursor.execute(query, *args)
            if query.lower().strip().startswith(('insert', 'update', 'delete')):
                self.connection.commit()
            if query.lower().strip().startswith('select'):
                columns = [column[0] for column in self.cursor.description]
                rows = self.cursor.fetchall()
                return [{columns[i]: row[i] for i in range(len(columns))} for row in rows]
        except pyodbc.Error as err:
            print(f"An error occurred while querying the database: {err}")
            if self.connection:
                self.connection.rollback()
    
    destruct_query_conditions = staticmethod(destruct_query_conditions)
    parse_sql_condition = staticmethod(parse_sql_condition)