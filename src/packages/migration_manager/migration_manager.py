import os
import json
from pathlib import Path

from datetime import datetime
from packages.workbook_manager import WorkbookManager
from packages.database_manager import DatabaseManager
from packages.file_manager import FileManager
from . import projects_sheet_append, proposals_sheet_append, members_sheet_append, awards_sheet_append, attachments_sheet_append, retrieve_pi_info

class MigrationManager:
    
    def __init__(self, db_manager: DatabaseManager, read_file_path: str):
        if not read_file_path:
            raise ValueError("A file path was not provided to the Workbook.")
        if not os.path.exists(read_file_path):
            raise ValueError(f"The Workbook Manager was provided an invalid file path: {read_file_path}")
        
        # Initialize an instance of the WorkbookManager class for the feedback file
        self.feedback_template_manager = WorkbookManager(read_file_path=read_file_path)
        
        # Initialize an instance of the WorkbookManager class for the generated data
        self.generated_template_manager = WorkbookManager()

        # Initialize an instance of the FileManager class for grant attachment files
        self.attachment_manager = FileManager(os.getenv("SAVE_PATH"), os.getenv("ATTACHMENT_PATH"))
        
        self.db_manager = db_manager
    
    def __enter__(self):
        self.attachment_manager.__enter__()
        self.retrieve_configs()
        self.retrieve_pi_info()
        self.retrieve_Disciplines()
        
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        current_time = datetime.now()
        formatted_time = current_time.strftime('%d_%m_%Y')
        self.generated_template_manager.save_changes(os.path.join(os.getenv("SAVE_PATH"), f"generated_data_{formatted_time}.xlsx"))
        self.attachment_manager.__exit__(exc_type, exc_value, traceback)
        
    def retrieve_configs(self):
        # Determine the path of the current module
        config_folder_path = Path(__file__).resolve().parent / 'config'
        
        # Retrieve template Sheets/Columns
        with open(config_folder_path / 'gen_sheets.json') as f:
            gen_sheets = json.load(f)
            for sheet_name, sheet_columns in gen_sheets.items():
                self.generated_template_manager.create_sheet(sheet_name, sheet_columns)
        
        # Retrieve Organization related Information
        with open(config_folder_path / 'john_jay_org_units.json') as f:
            self.ORG_UNITS = json.load(f)
        with open(config_folder_path /'john_jay_centers.json') as f:
            self.ORG_CENTERS = json.load(f)
        with open(config_folder_path / 'john_jay_external_orgs.json') as f:
            self.ORGANIZATIONS = json.load(f)
        self.ALL_ORGS = {
            **self.ORGANIZATIONS['existing_external_orgs'],
            **self.ORGANIZATIONS['non_existing_external_orgs']
        }

        # Retrieve Instrument/Activity Types
        with open(config_folder_path / 'associated_data.json', 'r') as f:
            associated_data = json.load(f)

        self.INSTRUMENT_TYPES = associated_data["instrument_types"]
        self.ACTIVITY_TYPES = associated_data["activity_types"]
        
    def retrieve_Disciplines(self):
        select_query = self.db_manager.select_query(
            table="LU_Discipline",
            cols=["ID", "Name"]
        )
        self.DISCIPLINES = {str(item['Name']) for item in select_query}
        
MigrationManager.projects_sheet_append = projects_sheet_append
MigrationManager.proposals_sheet_append = proposals_sheet_append
MigrationManager.members_sheet_append = members_sheet_append
MigrationManager.awards_sheet_append = awards_sheet_append
MigrationManager.attachments_sheet_append = attachments_sheet_append
MigrationManager.retrieve_pi_info = retrieve_pi_info