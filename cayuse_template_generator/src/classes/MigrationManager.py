import multiprocessing
from math import ceil
import pandas as pd
import math
import json
import re
from dotenv import load_dotenv
from methods.utils import find_email_by_username
# Load environment variables from .env file
load_dotenv("../env/.env.development")

import os

from classes.DatabaseManager import DatabaseManager
from classes.TemplateManager.TemplateManager import TemplateManager

# from sheets.projects import project_sheet_manager
# from sheets.proposals import proposal_sheet_manager
# from sheets.members import members_sheet_manager
from sheets.proposals import proposals_sheet_append
from sheets.members import members_sheet_append
from sheets.projects import projects_sheet_append
from sheets.awards import awards_sheet_append

class MigrationManager:
    INVESTIGATORS_ALT = {}

    def __init__(self):
        # Initialize an instance of the TemplateManager class for the feedback file
        self.feedback_template_manager = TemplateManager(os.getenv('EXCEL_FILE_PATH'), os.path.join(os.getenv('SAVE_PATH'), 'cayuse_template_data_logs.json'))

        # Open the JSON file that contains the data regarding the sheets to be created
        with open('./config/gen_sheets.json') as f:
            # Load the JSON data into a dictionary
            gen_sheets = json.load(f)
            
        # Initialize an instance of the TemplateManager class for the generated data
        self.generated_template_manager = TemplateManager(log_file_path=(os.path.join(os.getenv("SAVE_PATH"), 'cayuse_generated_template_data_logs.json')), create_sheets=({sheet: {col:[] for col in sheet_props} for sheet,sheet_props in gen_sheets.items()}))

        # Initialize an instance of the DatabaseMananger class
        self.db_manager = DatabaseManager(os.path.join(os.getenv('SAVE_PATH'), 'cayuse_database_data_logs.json'))
        # Initialize the connection to the database
        self.db_manager.init_db_conn(os.getenv('ACCESS_DB_PATH'))

    def __enter__(self):
        self.retrieve_PI_Info()
        self.retrieve_ORG_Info()
        self.retrieve_Disciplines()
        self.retrieve_Instrument_Types()
                    
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):     
        generated_data = dict()
        for sheet_name, sheet_props in self.feedback_template_manager.df.items():
            generated_data[sheet_name] = sheet_props.to_dict()
        self.generated_template_manager.save_changes(os.path.join(os.getenv('SAVE_PATH'), 'generated_data.xlsx'))
        
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
        
    def retrieve_ORG_Info(self):
        # Retrieve Organization related Information
        with open('./config/john_jay_org_units.json') as f:
            self.ORG_UNITS = json.load(f)
        with open('./config/john_jay_centers.json') as f:
            self.ORG_CENTERS = json.load(f)
        with open('./config/john_jay_external_orgs.json') as f:
            self.ORGANIZATIONS = json.load(f)
        
    def retrieve_Disciplines(self):
        select_query = self.db_manager.execute_query("SELECT * FROM LU_Discipline")
        self.DISCIPLINES = {int(item['ID']):item['Name'] for item in select_query}
        
    def retrieve_Instrument_Types(self):
        relevant_data = None
        with open('./config/john_jay_instrument_and_activity_types.json') as f:
            relevant_data = json.load(f)
            
        self.INSTRUMENT_TYPES = relevant_data["instrument_types"]
        self.ACTIVITY_TYPES = relevant_data['activity_types']

    def start_migration(self, grants):
        self.awards_sheet_append(grants)
            
MigrationManager.projects_sheet_append = projects_sheet_append
MigrationManager.proposals_sheet_append = proposals_sheet_append
MigrationManager.members_sheet_append = members_sheet_append
MigrationManager.awards_sheet_append = awards_sheet_append