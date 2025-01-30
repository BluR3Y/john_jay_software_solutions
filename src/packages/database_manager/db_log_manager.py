import os

from modules.log_manager import LogManager

# Use Inheritance to create a child class for database logs
class DatabaseLogManager(LogManager):
    def __init__(self, log_file_path: str):
        if not log_file_path:
            raise ValueError("A file path was not provided to the Database LogManager.")
        
        # Call the parent class constructor
        super().__init__(log_file_path)
        
    def append_log(self, process: str, table: str, row_identifier: str, rows: dict, updates: dict):
        logs = dict()
        for row in rows:
            row_log = dict()
            for col in row.keys():
                if col != row_identifier:
                    row_log[col] = f"{row[col]}:{updates[col]}"
            logs[row[row_identifier]] = row_log
        new_logs = {table: logs}
        
        # Use the parent class method to append the process logs
        super().append_runtime_log(process, new_logs)
        
# To save created logs: call parent method "save_logs"