import os
import pandas as pd
import openpyxl
import pathlib

from workbook_manager.comment_manager import CommentManager
from workbook_manager.workbook_log_manager import WorkbookLogManager

class WorkbookManager:
    read_file_path = None
    
    def __init__(self, read_file_path: str = None, create_sheets: dict = None, log_file_path: str = None):
        if read_file_path:
            if not os.path.exists(read_file_path):
                raise Exception("The WorkbookManager was provided an invalid file path: ", read_file_path)
                    
            # Store the read file's path
            self.read_file_path = read_file_path
            # Read the contents of the workbook
            self.df = pd.read_excel(read_file_path, sheet_name=None)
            log_path_obj = pathlib.Path(log_file_path)
            log_file_path = os.path.join(log_path_obj, f"{log_path_obj.stem}.json")
        elif create_sheets:
            if not log_file_path:
                raise ValueError("The WorkbookManager was not provided a file path for logs.")
            
            self.df = {sheet_name: pd.DataFrame({col_name: col_data for col_name, col_data in props.items()})
                       for sheet_name, props in create_sheets.items()}
        else:
            raise Exception("Neither a file path or a list of sheet names were provided to the WorkbookManager.")
        
        # Initialize an instance of the Comment Manager
        self.comment_manager = CommentManager(read_file_path, self.df.keys())
        
        # Initialize an instance of the Logger
        self.log_manager = WorkbookLogManager(log_file_path)
        
    def update_cell(self, process: str, sheet: str, row: int, col: int, new_val):
        if sheet not in list(self.df.keys()):
            raise ValueError(f"THe sheet with the name '{sheet}' does not exist in the workbook.")
        
        sheet_data_frame = self.df[sheet]
        cell_prev_value = sheet_data_frame.iloc[row][col]
        sheet_data_frame.loc[row, col] = new_val
        self.log_manager.append_log(
            process,
            sheet,
            row,
            col,
            cell_prev_value,
            new_val
        )
        
    def append_row(self, sheet: str, props: dict):
        # Create a new DataFrame
        new_row = pd.DataFrame({key: [value] for key, value in props.items()})
        # Append using pd.concat
        self.df[sheet] = pd.concat([self.df[sheet], new_row], ignore_index=True)
        
    def get_entry(self, sheet_name: str, conditions: dict, value: any, all: bool = False):
        try:
            # Retrieve the sheet
            sheet_data_frame = self.df[sheet_name]
            # Last Here