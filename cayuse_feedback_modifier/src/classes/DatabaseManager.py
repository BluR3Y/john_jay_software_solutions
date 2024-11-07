import pyodbc
import os

# Created a class to encapsulate the database logic and make it reusable
# Approach improves resource management by initializing and terminating the connection in the class's constructor and destructor
class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def __enter__(self):
        """ Initialize the database connection when entering the context. """
        self.init_db_conn()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        """ Close the database connection when exiting the context. """
        self.terminate_db_conn()

    def init_db_conn(self):
        """ Initialize the database connection. """
        try:
            # Open the connection
            self.connection = pyodbc.connect(
                r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
                r'DBQ=' + os.getenv("ACCESS_DB_PATH") + ';'
            )
            self.cursor = self.connection.cursor()
        except pyodbc.Error as err:
            print(f"An error occured while connecting to the database: {err}")

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

    def terminate_db_conn(self):
        """Terminate the database connection."""
        if self.connection:
            try:
                self.cursor.close()
                self.connection.close()
            except pyodbc.Error as err:
                print(f"An error occurred while closing the connection: {err}")