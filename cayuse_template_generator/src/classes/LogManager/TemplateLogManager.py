import json
import datetime
import os

from classes.LogManager.LogManager import LogManager

# Use inheritance to create a child class for Template logs
class TemplateLogManager(LogManager):
    def __init__(self, log_file_path):
        # Call the parent class constructor
        super().__init__(log_file_path)

    # Method will add Template logs to the logger
    def append_log(self, process, sheet, row, col, prev_val, new_val):
        """Add detailed logs with shet, row, and column information."""
        # Build the hierarchical structure for the logs
        new_log = {sheet: {row: {col: f"{prev_val}:{new_val}"}}}

        # Use the parent class method to append the process logs
        super().append_runtime_log(process, new_log)