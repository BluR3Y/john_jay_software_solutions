import pyodbc
import os
import datetime
from typing import Union

from . import DatabaseLogManager, destruct_query_conditions, parse_sql_condition

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
        self.log_manager = DatabaseLogManager(os.path.join(log_file_dir, "database_logs.json"))
        
    # Only envoked when using "with"(context manager)
    def __enter__(self):
        """Initialize the database connection when entering the context."""
        self.init_db_connection()
        return self
    
    # Only envoked when using "with"(context manager)
    def __exit__(self, exc_type, exc_value, traceback):
        """Close the database connection when exiting the context."""
        self.terminate_db_connection()
        
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
        
    def terminate_db_connection(self):
        """Terminate the database connection."""
        if self.connection:
            try:
                self.cursor.close()
                self.connection.close()
            except pyodbc.Error as err:
                raise ConnectionError(f"An error occured while closing the database: {err}")
        # Save logger changes
        self.log_manager.save_logs()
        
    def get_db_tables(self):
        tables = []
        for row in self.cursor.tables():
            if row.table_type == "TABLE":
                tables.append(row.table_name)
        return tables

    def get_table_columns(self, table):
        """Retrieve table columns."""
        try:
            query = f"SELECT * FROM {table} WHERE 1=0"
            self.cursor.execute(query)
            columns = [column[0] for column in self.cursor.description]
            return columns
        except pyodbc.Error as err:
            print(f"An error occurred while querying the database: {err}")
            if self.connection:
                self.connection.rollback()
    
    def select_query(self, table: str, cols: list[Union[str, tuple]] = None, conditions: dict = None, limit: int = None) -> list[dict]:
        """Execute a 'SELECT' query to the database."""
        db_tables = self.get_db_tables()
        if table not in db_tables:
            raise ValueError(f"The table '{table}' does not exist in the database.")

        formatted_limit = f"TOP {limit}" if limit else ""
        formatted_cols = ', '.join([(f"{col[0]} AS {col[1]}" if isinstance(col, tuple) else col) for col in cols]) if cols else '*'
        query = f"SELECT {formatted_limit} {formatted_cols} FROM {table}"
        values = []

        if conditions:
            cond_str, cond_vals = self.destruct_query_conditions(conditions)

            query += f" WHERE {cond_str}"
            values = cond_vals
            
        # Execute query
        self.cursor.execute(query, values)
        
        rows = self.cursor.fetchall()
        return [dict(zip([column[0] for column in self.cursor.description], row)) for row in rows] if rows else []
    
    def update_query(self, table: str, cols: dict[str, Union[None, str, int, bool, datetime.date]], conditions: dict = None):
        "Execute an update query."
        try:
            if table not in self.get_db_tables():
                raise ValueError(f"The table '{table}' does not exist in the database.")
            if not cols:
                raise ValueError("No columns provided for update.")
            
            table_columns = self.get_table_columns(table)
            table_row_identifier = table_columns[0]
            affecting_rows = self.select_query(table, [table_row_identifier, *cols.keys()], conditions)
            
            if not affecting_rows:
                raise ValueError("Could not find records that satisfied given parameters.")
            
            for row in affecting_rows:
                changing_fields = {key:{"prev_value": row[key], "new_value": val} for key, val in cols.items() if (key in row and row[key] != val)}
                if not changing_fields:
                    continue
                
                row_id = row[table_row_identifier]
                formatted_cols = ', '.join([f"{col} = ?" for col in changing_fields.keys()])
                query_str = f"UPDATE {table} SET {formatted_cols} WHERE {table_row_identifier} = ?"
                query_vals = [values['new_value'] for values in changing_fields.values()]

                self.cursor.execute(query_str, [*query_vals, row_id])
                
                self.log_manager.append_runtime_log(self.process, {row_id: changing_fields})
            
            self.connection.commit()
        except ValueError as err:
            print(f"ValueError: {err}")
            if self.connection:
                self.connection.rollback()
                
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