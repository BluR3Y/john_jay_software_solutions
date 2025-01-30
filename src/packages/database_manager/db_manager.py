import pyodbc
import pathlib
import os

from db_log_manager import DatabaseLogManager

class DatabaseManager:
    def __init__(self, db_path: str):
        if not db_path:
            raise ValueError("A database file path was not provided to the DatabaseManager.")
        if not os.path.exists(db_path):
            raise ValueError(f"No database exists at the path: {db_path}")
        
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        log_file_dir = pathlib.Path(db_path)
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
        
# Missing querying methods