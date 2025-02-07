import os
import re
import json
from pathlib import Path

from datetime import datetime
from packages.workbook_manager import WorkbookManager
from packages.database_manager import DatabaseManager
from . import projects_sheet_append, proposals_sheet_append, members_sheet_append, awards_sheet_append, attachments_sheet_append

class MigrationManager:
    
    def __init__(self, db_manager: DatabaseManager, read_file_path: str, save_path: str = None):
        if not read_file_path:
            raise ValueError("A file path was not provided to the Workbook.")
        if not os.path.exists(read_file_path):
            raise ValueError(f"The Workbook Manager was provided an invalid file path: {read_file_path}")
        
        # Initialize an instance of the WorkbookManager class for the feedback file
        self.feedback_template_manager = WorkbookManager(read_file_path=read_file_path)
        
        # Initialize an instance of the WorkbookManager class for the generated data
        self.generated_template_manager = WorkbookManager()
        
        self.save_path = save_path
        self.db_manager = db_manager
    
    def __enter__(self):
        self.retrieve_configs()
        self.retrieve_PI_Info()
        self.retrieve_Disciplines()
        
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        current_time = datetime.now()
        formatted_time = current_time.strftime('%d_%m_%Y')
        self.generated_template_manager.save_changes(os.path.join(self.save_path, f"generated_data_{formatted_time}.xlsx"))
    
    def retrieve_PI_Info(self):
        investigators = {}
        pi_fragments = {}
        people_dataframe = self.feedback_template_manager.df["Data - People"]
        people_sheet_length, people_sheet_width = people_dataframe.shape
        people_rows = people_dataframe.iloc[1:people_sheet_length - 1]
        for index, person in people_rows.iterrows():
            first_name = person[0].strip().capitalize()
            middle_name = (person[1] if isinstance(person[1], str) else "").strip().capitalize()
            last_name = person[2].strip().capitalize()
            email = person[4]
            empl_id = None
            
            enclosed_regex = r".*\(\d{8}\)$"
            if re.match(enclosed_regex, last_name):
                last_name, empl_id = last_name.split("(")
                empl_id = str(empl_id[:-1])
            else:
                empl_id = str(person[3])
            
            if not empl_id in investigators:
                investigators[empl_id] = {
                    "name": {
                        "first": first_name,
                        "middle": middle_name,
                        "last": last_name
                    },
                    "email": email
                }
            else:
                raise Exception("Duplicate investigator in 'Data - People' sheet")
            
        association_dataframe = self.feedback_template_manager.df["Data - Associations"]
        for index, associate in association_dataframe.iterrows():
            pi_empl_id = str(associate["EMP ID"])
            if pi_empl_id:
                pi_association = associate["ASSOCIATION"]
                if pi_association:
                    if pi_empl_id in investigators:
                        investigators[pi_empl_id]["association"] = pi_association
                    else:
                       pi_fragments[pi_empl_id] = {
                           "email": associate["USERNAME"],
                           "association": pi_association
                       }
                else:
                    raise Exception("Investigator is missing Association in 'Data - Associations' sheet")
            else:
                raise Exception("Investigator is missing Employee ID in 'Data - Associations' sheet")
            
        # Missing: Logic that fills in missing information for investigators in 'Data - Association' sheet
        # # Retrieve Primary Investigator Information
        # template_pull = self.feedback_template_manager.df["Data - Associations"][['USERNAME','ASSOCIATION']]
        # pi_info = dict()
        # for index, row in template_pull.iterrows():
        #     pi_info[row['USERNAME']] = row['ASSOCIATION']
        # pi_emails = [str(email) for email in pi_info.keys()]
        # res = self.db_manager.execute_query("SELECT PI_name FROM PI_name")
        # pi_names = set(pi['PI_name'] for pi in res)
        
        # for pi in pi_names:
        #     if pi:
        #         try:
        #             if ',' in pi:
        #                 l_name, f_name = pi.split(", ")
        #             else:
        #                 l_name, f_name = pi.rsplit(' ')
        #         except ValueError:
        #             continue
        #         closest_match = find_email_by_username(f_name, l_name, pi_emails)
        #         if closest_match:
        #             self.pi_data[f"{l_name}, {f_name}"] = {
        #                 "email": closest_match,
        #                 "association": pi_info[closest_match]
        #             }
        
        self.INVESTIGATORS = investigators
        
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
            
        # Retrueve Instrument/Activty Types
        with open(config_folder_path / 'john_jay_instrument_and_activity_types.json', 'r') as f:
            relevant_data = json.load(f)
            
        self.INSTRUMENT_TYPES = relevant_data["instrument_types"]
        self.ACTIVITY_TYPES = relevant_data['activity_types']
        
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