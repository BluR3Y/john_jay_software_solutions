from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv("../env/.env.development")

import pandas as pd
import pyodbc
import os
import json

import configs.db_config as db_config
import configs.openai_config as openai_config
import sheets.members as members
import sheets.attachments as attachments

class FeedBackModifier:
    
    def __init__(self):
        # Access excel file path from environment variable
        self.filepath = os.getenv('EXCEL_FILE_PATH')
        # Read Excel file
        self.df = pd.read_excel(self.filepath, sheet_name=None)
        # print(self.df.items())
        self.logger = {
            'filename': os.path.basename(self.filepath),
            'modifications': dict()
        }

    # Save changes to excel file
    def save_excel_changes(self, as_copy = True, index=False):
        try:
            save_path = self.filepath
            file_dir = os.path.dirname(save_path)
            file_name = os.path.basename(save_path)

            if (as_copy):
                save_path = f"{file_dir}\\{os.path.splitext(file_name)[0]} - modified_copy.xlsx"

            # Use ExcelWriter to write multiple sheets back into the Excel file
            with pd.ExcelWriter(save_path, engine='openpyxl', mode='w') as writer:
                for sheet_name, df_sheet in self.df.items():
                    # Leave index as False if you don't want to save the index column from the DataFrame
                    df_sheet.to_excel(writer, sheet_name=sheet_name, index=index)

            # Log the modifications
            with open(file_dir + '/excel_modifier_logger.json', 'w') as json_file:
                json.dump(self.logger, json_file)
        except Exception as e:
            print(f"Error saving Excel file: {e}")
        
FeedBackModifier.execute_query = db_config.execute_query
FeedBackModifier.modify_username = members.modify_entries
FeedBackModifier.verify_entries = attachments.verify_entries

# Testing the Modifier class:
if __name__ == "__main__":
    # Create a new class instance
    my_instance = FeedBackModifier()


    # my_instance.modify_username()
    my_instance.verify_entries()


    # Save document changes
    my_instance.save_excel_changes()