import pyodbc

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

    def select_query(self, table: str, cols: list[str], condition=None, *args) -> list[dict]:
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

    def update_query(self,process: str, table: str, cols: dict[str, any], condition=None, *args):
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