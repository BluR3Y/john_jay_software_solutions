import json
import datetime
import os

from modules.log_manager import LogManager

# Use inheritance to create a child class for Workbook logs
def WorkbookLogManager(LogManager):
    def __init__(self, log_file_path: str):
        if not log_file_path:
            raise ValueError("A file path for logs was not provided to Workbook LogManager.")
        
        # Call the parent class constructor
        super().__init__(log_file_path)
        
    # Method will add Template logs to the logger
    def append_log(self, process: str, sheet: str, row: int, col: int, prev_val: any, new_val: any):
        """Add detailed logs with sheet, row, and column information."""
        # Build the hierchical structure for the logs
        new_log = {sheet: {row: {col: f"{prev_val}:{new_val}"}}}
        
        # Use the parent class method to append the process logs
        super().append_runtime_log(process, new_log)