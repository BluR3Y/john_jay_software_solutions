import os

from packages.workbook_manager import WorkbookManager

class MigrationManager:
    
    def __init__(self, read_file_path: str, save_path: str = None):
        if not read_file_path:
            raise ValueError("A file path was not provided to the Workbook.")
        if not os.path.exists(read_file_path):
            raise ValueError(f"The Workbook Manager was provided an invalid file path: {read_file_path}")
        
        # Initialize an instance of the WorkbookManager class for the feedback file
        self.feedback_template_manager = WorkbookManager(
            read_file_path=read_file_path,
            log_file_path=()
        )
    
    def __enter__(self):
        pass
    
    def __exit__(self):
        pass
    
# Missing