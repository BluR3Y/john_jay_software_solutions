from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv("../env/.env.development")

import openpyxl.comments
import pandas as pd
import os
import json
import argparse
import datetime
import openpyxl

import configs.db_config as db_config
import configs.openai_config as openai_config
import sheets.members as members
import sheets.attachments as attachments
import sheets.awards as awards
import sheets.proposals as proposals

class FeedBackModifier:
    
    def __init__(self):
        # Access excel file path from environment variable
        self.filepath = os.getenv('EXCEL_FILE_PATH')
        # Read Excel file
        self.df = pd.read_excel(self.filepath, sheet_name=None)

        self.comment_cache = dict()
        self.logger = {
            'filename': os.path.basename(self.filepath),
            'timestamp': str(datetime.date.today()),
            'sheets': dict()
        }

    # Save changes to excel file
    def save_excel_changes(self, as_copy = True, index=False):
        try:
            save_path = os.getenv('COPY_SAVE_PATH') if as_copy and os.getenv('COPY_SAVE_PATH') else os.path.dirname(self.filepath)
            file_name = f"{os.path.splitext(os.path.basename(self.filepath))[0]}{f" - modified_copy_{datetime.datetime.today().strftime('%m-%d-%Y')}" if as_copy else ''}.xlsx"
            full_path = os.path.join(save_path, file_name)

            # Use ExcelWriter to write multiple sheets back into the Excel file
            with pd.ExcelWriter(full_path, engine='openpyxl', mode='w') as writer:
                for sheet_name, df_sheet in self.df.items():
                    # Leave index as False if you don't want to save the index column from the DataFrame
                    df_sheet.to_excel(writer, sheet_name=sheet_name, index=index)

            # Load the workbook
            workbook = openpyxl.load_workbook(full_path)
            for sheet_name in self.comment_cache:
                if sheet_name in workbook.sheetnames:
                    sheet_content = workbook[sheet_name]
                    for cell_position in self.comment_cache[sheet_name]:
                        cell = sheet_content[cell_position]
                        cell.comment = openpyxl.comments.Comment(self.comment_cache[sheet_name][cell_position], "Developer")
                else:
                    raise Exception(f"The sheet with the name '{sheet_name}' does not exist in the workbook")
            # Save the workbook with comments
            workbook.save(full_path)

            # # Log the modifications
            with open(save_path + f"/excel_modifier_logger_{datetime.datetime.today().strftime('%m-%d-%Y')}.json", 'w') as json_file:
                json.dump(self.logger, json_file)
        except Exception as e:
            print(f"Error saving Excel file: {e}")

    # Adds process logs to the object's logger
    def append_process_logs(self, sheet, logs):
        # If no prior logs have been created for the provided sheet, initialize the property in the logger
        if sheet not in self.logger['sheets']:
            self.logger['sheets'][sheet] = logs
        # Else, add the properties of the sheet to the class logger
        else:
            self.logger['sheets'][sheet].update(logs)

    # Add cell comments to the object's comment cache
    def append_cell_comments(self, sheet, cell, comment):
        if sheet not in self.comment_cache:
            self.comment_cache[sheet] = { cell: comment }
        else:
            self.comment_cache[sheet].update({ cell: comment })
        
FeedBackModifier.execute_query = db_config.execute_query
FeedBackModifier.modify_username = members.modify_entries
FeedBackModifier.verify_entries = attachments.verify_entries
FeedBackModifier.get_missing_project_attachments = attachments.missing_project_attachments
FeedBackModifier.get_project_info = attachments.retrieve_project_info
FeedBackModifier.populate_db_award_discipline = awards.populate_db_discipline
FeedBackModifier.populate_template_award_discipline = awards.populate_template_discipline
FeedBackModifier.populate_template_award_department = awards.populate_template_department
FeedBackModifier.populate_template_proposal_department = proposals.populate_template_department

# Testing the Modifier class:
if __name__ == "__main__":
    ## Create a new class instance
    my_instance = FeedBackModifier()

    # Initialize the argument parser
    parser = argparse.ArgumentParser(description="Parser handles command-line flags.")

    # Add optional flags and arguments
    # parser.add_argument('--save', '-s', type=str, help='Save changes to original file or as a copy')
    parser.add_argument('--methods', '-m', nargs='+', help='List of methods to call.')

    # Parse the arguments
    args = parser.parse_args()

    if args.methods:
        for method in args.methods:
            if hasattr(my_instance, method) and callable(getattr(my_instance, method)):
                getattr(my_instance, method)()
            else:
                raise Exception(f"The method {method} does not exist")
        # Save document changes
        my_instance.save_excel_changes()

