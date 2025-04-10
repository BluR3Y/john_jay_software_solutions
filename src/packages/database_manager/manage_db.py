from packages.database_manager import DatabaseManager
from pprint import pprint

from modules.utils import request_file_path, multi_select_input, single_select_input, request_user_confirmation

PROCESS_NAME = "Manage Database"

def view_logs(db_manager: DatabaseManager):
    try:
        log_manager = db_manager.log_manager
        selected_date = single_select_input("Select date logs:", list(log_manager.get_runtime_dates()))
        date_logs = log_manager.get_runtime_logs(selected_date)
        log_processes = list(date_logs.keys())

        selected_process = multi_select_input("Select processes from logs:", log_processes)
        logs = {process:date_logs[process] for process in selected_process}
        pprint(logs)
    except Exception as err:
        print(f"An unexpected error occured: {err}")

def revert_changes(db_manager: DatabaseManager):
    try:
        log_manager = db_manager.log_manager
        selected_date = single_select_input("Select date logs:", list(log_manager.get_runtime_dates()))
        date_logs = log_manager.get_runtime_logs(selected_date)

        pprint(date_logs)
        if not request_user_confirmation("Revert following changes?"):
            print("Cancelled revertion")
            return

        for process, items in date_logs.items():
            for table, records in items.items():
                table_columns = db_manager.get_table_columns(table)
                table_id_name, table_id_type = list(table_columns.items())[0]
                for identifier, properties in records.items():
                    db_manager.update_query(table,{
                        name:props['prev_value'] for name,props in properties.items()
                    },{
                        table_id_name:{ "operator": "=", "value": identifier }
                    })
        print(f"Successfully reverted database changes made on: {selected_date}")     
    except Exception as err:
        print(f"An unexpected error occured: {err}")

def manage_database(db_path: str):
    with DatabaseManager(db_path, PROCESS_NAME) as db_manager:
        print(f"Current Process: {PROCESS_NAME}")
        while True:
            user_selection = single_select_input("Select a Database Manager Action:",[
                "View changes",
                "Revert changes",
                "Exit Process"
            ])

            match user_selection:
                case "View changes":
                    view_logs(db_manager)
                case "Revert changes":
                    revert_changes(db_manager)
                case _:
                    return