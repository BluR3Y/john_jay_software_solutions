from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv("../env/.env.development")

import pandas as pd
import os
import json
import datetime
import inspect

from classes.DatabaseManager import DatabaseManager

import sheets.attachments as attachments
import sheets.members as members
import sheets.awards as awards
import sheets.proposals as proposals
import sheets.others as others

from methods import logger
from methods import comment

class FeedBackModifier:
    # Variable that will store comments before creating them in the excel file
    comment_cache = dict()

    def __init__(self):
        # Read Excel file
        self.df = pd.read_excel(os.getenv('EXCEL_FILE_PATH'), sheet_name=None)
        # Store the sheet names
        self.sheets = list(self.df.keys())

        self.db_manager = DatabaseManager()
        self.db_manager.init_db_conn()

        # Variable that will store the path of the json file that will store the logs
        self.logs_path = os.path.join(os.getenv('SAVE_PATH') or os.path.dirname(self.filepath), 'cayuse_data_migration_logs.json')
        # If the file exists:
        if os.path.exists(self.logs_path):
            # Store the logs in a variable
            with open(self.logs_path) as json_file:
                self.logs = json.load(json_file)
        else:
            # Initialize an empty dictionary
            self.logs = dict()

        all_processes = dict()
        for sheet_methods in [awards, proposals, members, attachments, others]:
            sheet_processes = dict()
            for fnName, fn in inspect.getmembers(sheet_methods, inspect.isfunction):
                process = fn(self)
                sheet_processes[process.name] = process
            all_processes[sheet_methods.SHEET_NAME] = sheet_processes
        self.processes = all_processes

    # Save changes to all related resources
    def save_changes(self, as_copy = True, index=False):
        try:
            excel_file_path = os.getenv('EXCEL_FILE_PATH')
            file_save_path = os.getenv('SAVE_PATH') if as_copy and os.getenv('SAVE_PATH') else os.path.dirname(excel_file_path)
            file_name = f"{os.path.splitext(os.path.basename(excel_file_path))[0]}{f" - modified_copy_{datetime.datetime.today().strftime('%m-%d-%Y')}" if as_copy else ''}.xlsx"
            full_path = os.path.join(file_save_path, file_name)

            # Use ExcelWriter to write multiple sheets back into the Excel file
            with pd.ExcelWriter(full_path, engine='openpyxl', mode='w') as writer:
                for sheet_name, df_sheet in self.df.items():
                    # Leave index as False if you don't want to save the index column from the DataFrame
                    df_sheet.to_excel(writer, sheet_name=sheet_name, index=index)

            # Create cell comments in excel file
            self.create_comments(full_path)
            # Save the changes made to the logger
            self.save_logs()

        except Exception as e:
            print(f"Error occured while saving changes: {e}")

# Logger related methods
FeedBackModifier.append_logs = logger.append_logs
FeedBackModifier.save_logs = logger.save_logs

# Comment related methods
FeedBackModifier.append_comment = comment.append_comment
FeedBackModifier.create_comments = comment.create_comments