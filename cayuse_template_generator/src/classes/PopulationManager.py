import pandas as pd

from sheets.projects import project_sheet_manager

class PopulationManager:
    def __init__(self):
        self.sheet_managers = [
            project_sheet_manager
        ]
        
    def populate_grant(self, grant):
        for fn in self.sheet_managers:
            fn.append_grant(grant)
            
    def save_changes(self, write_file_path, index=False):
        # Use ExcelWriter to write multiple sheets back into the Excel file
        with pd.ExcelWriter(write_file_path, engine='openpyxl', mode='w') as writer:
            for sheet_manager in self.sheet_managers:
                sheet_manager.df.to_excel(writer, sheet_name=sheet_manager.sheet_name, index=False)