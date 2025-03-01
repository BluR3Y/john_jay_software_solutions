import argparse
import os
import warnings
import pandas as pd
# from packages.workbook_manager.workbook_manager import WorkbookManager
# from packages.workbook_manager.series_ref import SeriesRef

warnings.simplefilter(action='ignore', category=FutureWarning)

from dotenv import load_dotenv
from modules.utils import request_user_selection
from packages.report_manager import manage_reports

from packages.database_manager import DatabaseManager
from packages.migration_manager import manage_migration

# Run the program
if __name__ == "__main__":
    user_actions = {
        "Fix Template": None,
        "Manage Reports": manage_reports,
        "Generate Template": manage_migration
    }
    
    # Initialize the argument parser
    parser = argparse.ArgumentParser(description="Parser handles command-line flags")
    # Add optional flags and arguments
    parser.add_argument(
        "--env", '-e',
        choices=["development","testing","production"],
        default="development",
        help="Select evironment type"
    )
    parser.add_argument(
        "--process", "-p",
        choices=user_actions.keys(),
        help="Select a process to run"
    )
    # parser.add_argument('--sheet', '-s', type=str, help="The name of the workbook sheet that the process belongs to.")
    # parser.add_argument('--process', '-p', action="append", help='Add process to call.')
    # parser.add_argument('--dev', action='store_true', help="Run process in developer mode.")
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Load environment variables from .env file
    file_path = os.path.realpath(__file__)
    file_dir = os.path.dirname(file_path)
    parent_dir = os.path.dirname(file_dir)
    load_dotenv(os.path.join(parent_dir, f"env/.env.{args.env}"))
    
    selected_process = args.process
    db_path = os.getenv('ACCESS_DB_PATH')
    if selected_process:
        process_script = user_actions[selected_process]
        process_script(db_path)
    else:
        while True:
            user_selection = request_user_selection("Select an action:", [*user_actions.keys(), "Exit Program"])
            if user_selection == "Exit Program":
                break
            
            action_fn = user_actions[user_selection]
            action_fn(db_path)