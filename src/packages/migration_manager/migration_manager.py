import os

from datetime import datetime
from packages.workbook_manager import WorkbookManager

class MigrationManager:
    
    def __init__(self, read_file_path: str, save_path: str = None):
        if not read_file_path:
            raise ValueError("A file path was not provided to the Workbook.")
        if not os.path.exists(read_file_path):
            raise ValueError(f"The Workbook Manager was provided an invalid file path: {read_file_path}")
        
        # Initialize an instance of the WorkbookManager class for the feedback file
        self.feedback_template_manager = WorkbookManager(read_file_path=read_file_path)
        
        # Initialize an instance of the WorkbookManager class for the generated data
        self.generated_template_manager = WorkbookManager()
        
        self.save_path = save_path
    
    def __enter__(self):
        
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        current_time = datetime.now()
        formatted_time = current_time.strftime('%d_%m_%Y')
        self.generated_template_manager.save_changes(os.path.join(self.save_path, f"generated_data_{formatted_time}.xlsx"))
    
    # Last Here: Do we need separate sheets?