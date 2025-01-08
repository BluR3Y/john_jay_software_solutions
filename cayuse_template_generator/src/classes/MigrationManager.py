from rich.progress import Progress
from math import ceil
import pandas as pd
import json
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv("../env/.env.development")

import os

from classes.DatabaseManager import DatabaseManager
from classes.CommentManager import CommentManager
from classes.TemplateManager import TemplateManager
from classes.PopulationManager import PopulationManager

class MigrationManager:
    next_avail_legacy_num = float('-inf')

    def __init__(self):
        # Initialize an instance of the TemplateManager class for the feedback file
        self.feedback_template_manager = TemplateManager(os.getenv('EXCEL_FILE_PATH'), os.path.join(os.getenv('SAVE_PATH'), 'cayuse_template_data_logs.json'))

        # Open the JSON file that contains the data regarding the sheets to be created
        with open('./config/gen_sheets.json') as f:
            # Load the JSON data into a dictionary
            gen_sheets = json.load(f)
        
        # Initialize an instance of the TemplateMananger class for the generated data
        # self.generated_template_manager = TemplateManager(
        #     log_file_path=(os.path.join(os.getenv('SAVE_PATH'), 'cayuse_generated_data_logs.json')),
        #     create_sheets=gen_sheets
        # )
        
        # Initialize an instance of the PopulationMananger class for the generated data
        self.generated_template_manager = PopulationManager()

        # Initialize an instance of the DatabaseMananger class
        self.db_manager = DatabaseManager(os.path.join(os.getenv('SAVE_PATH'), 'cayuse_database_data_logs.json'))
        # Initialize the connection to the database
        self.db_manager.init_db_conn(os.getenv('ACCESS_DB_PATH'))

        # Initialize an instance of the CommentManager class
        self.comment_manager = CommentManager(os.getenv('EXCEL_FILE_PATH'))

    def __enter__(self):
        res = self.db_manager.execute_query("SELECT grant_id FROM grants")
        self.grant_ids = [grant['grant_id'] for grant in res]

        # Used to generate new projectLegacyNumber for grants not already assigned one
        proposal_data_frame = self.feedback_template_manager.df["Proposal - Template"]
        grants_proposal_legacy_nums = proposal_data_frame["projectLegacyNumber"].tolist()
        for legacy_num in grants_proposal_legacy_nums:
            self.next_avail_legacy_num = max(legacy_num, self.next_avail_legacy_num)
        self.next_avail_legacy_num += 1

        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
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
                    self.append_grant(grant)
                    break

                # Update progress bar after processing the batch
                progress.update(task, advance=1)

    def append_grant(self, grant):
        template_entry_data = self.feedback_template_manager.get_entry("Proposal - Template", "proposalLegacyNumber", grant['Grant_ID'])
        if isinstance(template_entry_data, pd.DataFrame):
            grant['projectLegacyNumber'] = template_entry_data['projectLegacyNumber']
        else:
            grant['projectLegacyNumber'] = self.next_avail_legacy_num
            self.next_avail_legacy_num += 1
        self.generated_template_manager.populate_grant(grant)