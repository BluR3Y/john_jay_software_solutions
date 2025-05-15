from packages.database_manager import DatabaseManager
from pprint import pprint
import os
import json
from packages.log_manager import LogManager
from packages.log_manager import manage_logs
from modules.utils import (
    request_file_path,
    single_select_input,
    request_user_confirmation
)

PROCESS_NAME = "Manage Database"

def view_logs(db_manager: DatabaseManager):
    log_manager = db_manager.log_manager
    selected_date = single_select_input("Select date logs:", list(log_manager.get_runtime_dates()))
    date_logs = log_manager.get_runtime_logs(selected_date)
    
    pprint(date_logs)

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

def apply_latest_changes(db_manager: DatabaseManager):
    latest_logs_path = request_file_path("Input file path of logs that will be applied to the database: ", [".json"])
    logs = {}
    with open(latest_logs_path, 'r', encoding='utf-8') as log_file:
        logs = json.load(log_file)
    
    def format_log(log):
        formatted = {}
        for key, props in log.items():
            if isinstance(props, dict):
                formatted[key] = format_log(props)
            elif key == "new_value":
                return props
        return formatted
    
    merged_logs = {}
    for log_timestamp in logs.keys():
        for lgs in logs[log_timestamp].values():
            db_manager.log_manager._merge_dicts(merged_logs, format_log(lgs))

    errors = []
    for table in merged_logs:
        table_cols = db_manager.get_table_columns(table)
        table_identifier = list(table_cols.keys())[0]
        for record_identifier, record_props in merged_logs[table].items():
            try:
                print(record_props)
            except Exception as err:
                errors.append(f"An error occured while updating record '{record_identifier}': {err}")
    if errors:
        print(f"Errors occured while applying latest changes: {errors}")

def delete_table_records(db_manager: DatabaseManager):
    selected_table = single_select_input("Select table to remove records from: ", db_manager.get_db_tables())
    table_columns = db_manager.get_table_columns(selected_table)
    record_identifier = list(table_columns.keys())[0]

    record_ids = None
    # From file or query
    source_conditions = single_select_input("Select source for search conditions:", ["Conditions Query","Identifier File"])
    if source_conditions == "Conditions Query":
        search_query = input("WHERE: ")
        if not search_query:
            raise ValueError("Failed to provide search query")
        
        formatted_query = db_manager.parse_sql_condition(search_query)
        print(f"Developer Info: {formatted_query}")

        search_result = db_manager.select_query(
            selected_table,
            [record_identifier],
            formatted_query
        )
        record_ids = [item[record_identifier] for item in search_result]
    else:
        conditions_path = request_file_path("Input the path of the text file with record ids:", [".txt"])
        with open(conditions_path, 'r') as conditions_file:
            ids = conditions_file.read().split(',')
        record_ids = ids
    print(f"Search returned {len(record_ids)} records")

    for record_id in record_ids:
        db_manager.delete_query(selected_table, {
            record_identifier: {
                "operator": "=",
                "value": record_id
            }
        })

def manage_database():
    with DatabaseManager(os.getenv("ACCESS_DB_PATH"), PROCESS_NAME) as db_manager:
        print(f"Current Process: {PROCESS_NAME}")
        while True:
            user_selection = single_select_input("Select a Database Manager Action:",[
                "View changes",
                "Revert changes",
                "Apply latest changes",
                "Delete Records",
                "Exit Process"
            ])

            match user_selection:
                case "View changes":
                    manage_logs(db_manager.log_manager)
                case "Revert changes":
                    revert_changes(db_manager)
                case "Apply latest changes":
                    apply_latest_changes(db_manager)
                case "Delete Records":
                    delete_table_records(db_manager)
                case _:
                    return