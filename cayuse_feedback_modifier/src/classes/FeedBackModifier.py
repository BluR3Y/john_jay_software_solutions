from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv("../env/.env.development")

import pandas as pd
import os
import datetime
import inspect

from classes.DatabaseManager import DatabaseManager
from classes.CommentManager import CommentManager
from classes.LogManager import LogManager
from classes.TemplateManager import TemplateManager

import sheets.attachments as attachments
import sheets.members as members
import sheets.awards as awards
import sheets.proposals as proposals
import sheets.projects as projects
import sheets.others as others

# *** Future version should make use of magic methods __enter__ and __exit__
class FeedBackModifier:

    def __init__(self):
        # Initialize an instance of the LogManager class
        # self.log_manager = LogManager(os.path.join(os.getenv('SAVE_PATH') or os.path.dirname(self.filepath), 'cayuse_data_migration_logs.json'))

        # Initialize an instance of the TemplateManager class
        self.template_manager = TemplateManager(os.getenv('EXCEL_FILE_PATH'), os.path.join(os.getenv('SAVE_PATH') or os.path.dirname(self.filepath), 'cayuse_data_migration_template_logs.json'))

        # Initialize an instance of the DatabaseManager class
        self.db_manager = DatabaseManager(os.path.join(os.getenv('SAVE_PATH') or os.path.dirname(self.filepath), 'cayuse_data_migration_database_logs.json'))
        self.db_manager.init_db_conn(os.getenv('ACCESS_DB_PATH'))

        # Initialize an instance of the CommentManager class
        self.comment_manager = CommentManager(os.getenv('EXCEL_FILE_PATH'))

        self.init_processes()

    def init_processes(self):
        all_processes = dict()
        for sheet_methods in [awards, proposals, projects, members, attachments, others]:
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

            # Save the changes made to the template
            self.template_manager.save_changes(full_path)
            # Create cell comments in excel file
            self.comment_manager.create_comments(full_path)

        except Exception as e:
            print(f"Error occured while saving changes: {e}")