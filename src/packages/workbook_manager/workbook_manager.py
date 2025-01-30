import os
import pandas as pd
import openpyxl

from workbook_manager.comment_manager import CommentManager

class WorkbookManager:
    read_file_path = None
    
    def __init__(self, read_file_path: str = None, log_file_path: str = None, create_sheets: dict = None):
        if read_file_path:
            if not os.path.exists(read_file_path):
                raise Exception("The WorkbookManager was provided an invalid file path: ", read_file_path)
                    
            # Store the read file's path
            self.read_file_path = read_file_path
            # Read the contents of the workbook
            self.df = pd.read_excel(read_file_path, sheet_name=None)
        elif create_sheets:
            pass
        else:
            raise Exception("Neither a file path or a list of sheet names were provided to the WorkbookManager.")
        
        self.comment_manager = CommentManager(read_file_path, self.df.keys())
        
        # Initialize an instance of the Logger
        # self.log_manager = WorkbookLogManager(log_file_path)