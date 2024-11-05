from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv("../env/.env.development")

import pandas as pd
import os
import json
import argparse
import datetime
import inspect

import configs.db_config as db_config
import sheets.attachments as attachments
import sheets.members as members
import sheets.awards as awards
import sheets.proposals as proposals
from methods import utils
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
        for sheet_methods in [awards, proposals, members, attachments]:
            if sheet_methods.SHEET_NAME in self.sheets:
                sheet_processes = dict()
                for fnName, fn in inspect.getmembers(sheet_methods, inspect.isfunction):
                    process = fn(self)
                    sheet_processes[process.name] = process
                all_processes[sheet_methods.SHEET_NAME] = sheet_processes
            else:
                raise Exception(f"The sheet '{sheet_methods.SHEET_NAME}' does not exist in the workbook")
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

# Database related methods
FeedBackModifier.execute_query = db_config.execute_query

# Logger related methods
FeedBackModifier.append_logs = logger.append_logs
FeedBackModifier.save_logs = logger.save_logs

# Comment related methods
FeedBackModifier.append_comment = comment.append_comment
FeedBackModifier.create_comments = comment.create_comments

# Run the program
if __name__ == "__main__":
    # Create a class instance
    my_instance = FeedBackModifier()

    # Initialize the argument parser
    parser = argparse.ArgumentParser(description="Parser handles command-line flags.")

    # Add optional flags and arguments
    parser.add_argument('--sheet', '-s', type=str, help="The name of the workbook sheet that the process belongs to.")
    parser.add_argument('--process', '-p', action="append", help='Add process to call.')

    # Parse the arguments
    args = parser.parse_args()
    if args:
        selected_sheet = args.sheet
        selected_processes = args.process
        if selected_sheet and selected_processes:
            if selected_sheet in my_instance.processes:
                for method in selected_processes:
                    if method in my_instance.processes[selected_sheet]:
                        my_instance.processes[selected_sheet][method].logic()
                    else:
                        raise Exception(f"The process '{method}' does not exist for the sheet '{selected_sheet}'.")
            else:
                raise Exception(f"The sheet '{selected_sheet}' does not exist in the workbook.")
            
            # Save changes
            my_instance.save_changes()
        else:
            raise Exception("Not all required arguments were passed.")