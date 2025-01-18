from rich.progress import Progress
from math import ceil
import pandas as pd
import json
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
    pi_data = dict()

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
        res = self.db_manager.execute_query("SELECT grant_id FROM grants;")
        self.grant_ids = [grant['grant_id'] for grant in res]
        
        # store pi_data
        # pi_info = [str(pi_email) for pi_email in self.feedback_template_manager.df["Data - Associations"][['USERNAME','ASSOCIATION']].tolist()]
        template_pull = self.feedback_template_manager.df["Data - Associations"][['USERNAME','ASSOCIATION']]
        pi_info = dict()
        for index, row in template_pull.iterrows():
            pi_info[row['USERNAME']] = row['ASSOCIATION']
        pi_emails = [str(email) for email in pi_info.keys()]
        res = self.db_manager.execute_query("SELECT PI_name FROM PI_name")
        pi_names = set(pi['PI_name'] for pi in res)
        
        for pi in pi_names:
            if pi:
                try:
                    if ',' in pi:
                        l_name, f_name = pi.split(", ")
                    else:
                        l_name, f_name = pi.rsplit(' ')
                except ValueError:
                    continue
                closest_match = find_email_by_username(f_name, l_name, pi_emails)
                if closest_match:
                    self.pi_data[f"{l_name}, {f_name}"] = {
                        "email": closest_match,
                        "association": pi_info[closest_match]
                    }

        return self
    
    def __exit__(self, exc_type, exc_value, traceback):     
        generated_data = dict()
        for sheet_name, sheet_props in self.feedback_template_manager.df.items():
            generated_data[sheet_name] = sheet_props.to_dict()
        self.generated_template_manager.save_changes(os.path.join(os.getenv('SAVE_PATH'), 'generated_data.xlsx'))

    def start_migration(self):
        grant_ids = self.grant_ids
        batch_limit = 40
        num_grants = len(grant_ids)
        total_batches = ceil(num_grants/batch_limit)
        
        # Create a task with a progress bar
        with Progress() as progress:
            task = progress.add_task("Processing", total=total_batches)

            last_index = 0
            while last_index < num_grants:
                new_end = last_index + batch_limit
                batch_ids = grant_ids[last_index:new_end]
                last_index = new_end

                # Perform the database query
                select_query = f"SELECT * FROM grants WHERE grant_id IN ({','.join(['?' for _ in batch_ids])})"
                query_res = self.db_manager.execute_query(select_query, batch_ids)

                # Process each grant
                for grant in query_res:
                    self.append_to_sheets(grant)

                # Update progress bar after processing the batch
                progress.update(task, advance=1)
                
    def append_grant(self, grant):
        for fn in self.sheet_managers:
            fn.append_grant(grant)
            
    def append_to_sheets(self, grant):
        self.projects_sheet_append(grant)
        # self.proposals_sheet_append(grant)
        # self.members_sheet_append(grant)
        
    
MigrationManager.proposals_sheet_append = proposals_sheet_append
MigrationManager.projects_sheet_append = projects_sheet_append
MigrationManager.members_sheet_append = members_sheet_append