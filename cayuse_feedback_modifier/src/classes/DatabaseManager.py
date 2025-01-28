import pyodbc
from typing import Union
import datetime

from classes.LogManager.DatabaseLogManager import DatabaseLogManager

# Created a class to encapsulate the database logic and make it reusable
# Approach improves resource management by initializing and terminating the connection in the class's constructor and destructor
class DatabaseManager:
    def __init__(self, log_file_path):
        self.connection = None
        self.cursor = None
        self.log_manager = DatabaseLogManager(log_file_path)

    def __enter__(self):
        """ Initialize the database connection when entering the context. """
        self.init_db_conn()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        """ Close the database connection when exiting the context. """
        self.terminate_db_conn()

    def init_db_conn(self, db_path):
        """ Initialize the database connection. """
        try:
            # Open the connection
            self.connection = pyodbc.connect(
                r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
                r'DBQ=' + db_path + ';'
            )
            self.cursor = self.connection.cursor()
        except pyodbc.Error as err:
            print(f"An error occured while connecting to the database: {err}")

    def terminate_db_conn(self):
        """Terminate the database connection."""
        if self.connection:
            try:
                self.cursor.close()
                self.connection.close()
            except pyodbc.Error as err:
                print(f"An error occurred while closing the connection: {err}")

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

    # caution: Deprecated
    def select_query_v1(self, table: str, cols: list[str], condition=None, *args) -> list[dict]:
        """Excecute a select SQL query."""
        try:
            query = f"SELECT {','.join(cols)} FROM {table}"
            if condition:
                query += " WHERE " + condition
            self.cursor.execute(query, *args)
            columns = [column[0] for column in self.cursor.description]
            rows = self.cursor.fetchall()
            return [{columns[i]: row[i] for i in range(len(columns))} for row in rows]
        except pyodbc.Error as err:
            print(f"An error occurred while querying the database: {err}")
            if self.connection:
                self.connection.rollback()
                
    def conditions_to_string(self, parsed_condition):
        # Helper function to format the condition back to string
        def format_condition(cond):
            if isinstance(cond, dict):
                # Handle logical operators (AND/OR)
                for operator in ['AND', 'OR']:
                    if operator in cond:
                        sub_conditions = cond[operator]
                        return f"({format_condition(sub_conditions[0])} {operator} {format_condition(sub_conditions[1])})"
                
                # Handle comparison operators and other conditions
                for column, details in cond.items():
                    operator = details['operator']
                    value = details['value']
                    
                    # Handle IN/NOT IN
                    if operator in ['IN', 'NOT IN']:
                        formatted_values = ', '.join([str(v) for v in value])
                        return f"{column} {operator} ({formatted_values})"
                    
                    # Handle BETWEEN
                    elif operator == 'BETWEEN':
                        return f"{column} {operator} {value[0]} AND {value[1]}"
                    
                    # Handle LIKE, NOT LIKE, REGEXP, NOT REGEXP
                    elif operator in ['LIKE', 'NOT LIKE', 'REGEXP', 'NOT REGEXP']:
                        return f"{column} {operator} {value}"
                    
                    # Handle IS NULL or IS NOT NULL
                    elif operator in ['IS', 'IS NOT']:
                        return f"{column} {operator} {value}"
                    
                    # Default: Comparison operators (e.g. =, <>, !=, <, <=, etc.)
                    else:
                        return f"{column} {operator} {value}"

            return str(cond)

        # Call the helper function with the top-level parsed condition
        return format_condition(parsed_condition)
    
    def select_query(self, table: str, cols: list[str], conditions: dict = None) -> list[dict]:
        """
        Execute a SELECT SQL query to the database
        """
        if not table:
            raise ValueError("Table name must be provided.")
        if not cols:
            raise ValueError("Columns list cannot be empty.")
        try:
            # Construct query
            query = f"SELECT {','.join(cols)} FROM {table}"
            
            if conditions:
                query += " WHERE " + self.conditions_to_string(conditions)
                
            # Execute query
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            
            # Convert results to list of dictionaries
            return [dict(zip([column[0] for column in self.cursor.description], row)) for row in rows]
        except pyodbc.Error as err:
            print(f"An error occured while querying the database: {err}")
            if self.connection:
                self.connection.rollback()

    # Caution: Deprecated
    def update_query_v1(self,process: str, table: str, cols: dict[str, any], condition=None, *args):
        """Execute an update query."""
        table_columns = self.get_table_columns(table)
        table_row_identifier = table_columns[0]
        affecting_rows = self.select_query(table, [table_row_identifier, *cols.keys()], condition, *args)

        if affecting_rows:
            try:
                query = f"UPDATE {table} SET {','.join(f"{col}=?" for col in cols.keys())}"
                if condition:
                    query += " WHERE " + condition
                self.cursor.execute(query, *cols.values(), *args)
                self.log_manager.append_log(process, table, table_row_identifier, affecting_rows, cols)
                self.connection.commit()
            except pyodbc.Error as err:
                print(f"An error occurred while querying the database: {err}")
                if self.connection:
                    self.connection.rollback()

    def update_query(self, process:str, table: str, cols: dict[str, Union[None,str,int, bool, datetime.date]], conditions = None) -> None:
        """ Execute an update query """
        try:
            table_columns = self.get_table_columns(table)
            table_row_identifier = table_columns[0]
            affecting_rows = self.select_query(table, [table_row_identifier, *cols.keys()], conditions)
            
            if not affecting_rows:
                raise Exception("Could not find record with given parameters.")
            
            query = f"UPDATE {table} SET {','.join(f"{col}=?" for col in cols.keys())}"
            if conditions:
                query += " WHERE " + self.conditions_to_string(conditions)
            print(query)
            self.cursor.execute(query, *cols.values())
            self.log_manager.append_log(process, table, table_row_identifier, affecting_rows, cols)
            self.connection.commit()
        except Exception as err:
            print("An error occured while updating records: ", err)
            if self.connection:
                self.connection.rollback()


    # ** Caution: Deprecated
    def execute_query(self, query, *args):
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
                
    # ** Caution: In Testing
    def execute_many_query(self, query, entries):
        """
        The method is both an efficient and scalable way of modifying multiple entries with unique values
        """
        try:
            # Begin a transaction
            self.connection.autocommit = False
            
            # Execute the query for each entry
            self.cursor.executemany(query, entries)
            
            # Commit the transaction
            self.connection.commit()
            print("All rows updated successfully.")
        except Exception as e:
            # Rollback the transaction on error
            self.connection.rollback()
            print(f"An error occured while executing database query: {e}")