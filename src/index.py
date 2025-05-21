import argparse
import os
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)

from dotenv import load_dotenv
from modules.utils import single_select_input
from modules.logger import logger

# from packages.report_manager import manage_reports
# from packages.migration_manager import manage_migration
# from packages.database_manager import manage_database
# from packages.workbook_manager_legacy import manage_workbook
# from packages.workbook_manager_beta.manage_workbook import manage_workbook as beta
from packages.workbook_manager import WorkbookManager

from scripts.manage_database import manage_database
from scripts.manage_reports import manage_reports
from scripts.manage_migration import manage_migration

# Run the program
if __name__ == "__main__":
    user_actions = {
        "Manage Reports": manage_reports,
        "Manage Database": manage_database,
        "Manage Migration": manage_migration,
        "Manage Workbook": None
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

    logger.config_logger(os.getenv("SAVE_PATH"), "debug")

    tester_one = WorkbookManager("C:/Users/reyhe/OneDrive/Documents/JJay/data_pull_2025_05_19/generated_data_accumulator_iter_1.xlsx").__enter__()
    tester_two = WorkbookManager("C:/Users/reyhe/OneDrive/Documents/JJay/data_pull_2025_05_19/generated_data_20_05_2025_iter_2.xlsx").__enter__()
    
    proposal_one = tester_one["Proposal - Template"]
    proposal_two = tester_two["Proposal - Template"]
    print(proposal_one.find_differences(proposal_two, ["proposalLegacyNumber"]))

    selected_process = args.process
    try:
        if selected_process:
            process_script = user_actions[selected_process]
            process_script()
        else:
            while True:
                user_selection = single_select_input("Select an action:", [*user_actions.keys(), "Exit Program"])
                if user_selection == "Exit Program":
                    break
                
                action_fn = user_actions[user_selection]
                action_fn()
    except Exception as err:
        logger.get_logger().exception(err)