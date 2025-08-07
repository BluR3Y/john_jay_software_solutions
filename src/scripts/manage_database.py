from packages.database_manager import DatabaseManager
from pprint import pprint
import os
import json
import datetime
from packages.log_manager import LogManager
from packages.log_manager import manage_logs
from modules.logger import logger
from modules.utils import (
    request_file_path,
    single_select_input,
    request_user_confirmation,
    multi_select_input
)

PROCESS_NAME = "Manage Database"

def view_logs(db_manager: DatabaseManager):
    log_manager = db_manager.log_manager
    selected_date = single_select_input("Select date logs", list(log_manager.get_runtime_dates()))
    date_logs = log_manager.get_runtime_logs(selected_date)
    
    pprint(date_logs)

def revert_changes(db_manager: DatabaseManager):
    try:
        log_manager = db_manager.log_manager
        selected_date = single_select_input("Select date logs", list(log_manager.get_runtime_dates()))
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
    source_db_path = request_file_path("Input file path of the database whose changes will be applied to the active database.", [".accdb"])
    with DatabaseManager(source_db_path, "Database Manager") as source_db:
        log_timestamps = source_db.log_manager.get_runtime_dates()
        if not log_timestamps:
            raise ValueError("No changes were detected from the source database.")

        selected_timestamps = multi_select_input("Select timestamp to apply its changes", log_timestamps)
        formatted_timestamps = [datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in selected_timestamps]
        formatted_timestamps.sort()
        compiled_changes = {}

        for timestamp in [datetime.datetime.strftime(ts, "%Y-%m-%d %H:%M:%S") for ts in formatted_timestamps]:
            logs = source_db.log_manager.get_runtime_logs(timestamp)
            for change in logs:
                if change.get("operation") == "update":
                    record_id = change.get('record_id')
                    properties = change.get('properties')
                    table = change.get('table')

                    # Missing other operations: CREATE, DELETE                    

                    change_structure = {
                        table: {
                            record_id: properties
                        }
                    }
                    db_manager.log_manager._merge_dicts(compiled_changes, change_structure)

        errors = []
        for table, record_changes in compiled_changes.items():
            for record, changes in record_changes.items():
                try:
                    table_columns = db_manager.get_table_columns(table)
                    table_id = list(table_columns.keys())[0]

                    latest_properties = source_db.select_query(
                        table,
                        cols=list(changes.keys()),
                        conditions={
                            table_id: {
                                "operator": "=",
                                "value": record
                            }
                        }
                    )
                    db_manager.update_query(
                        table,
                        cols=latest_properties[0],
                        conditions={
                            table_id: {
                                "operator": "=",
                                "value": record
                            }
                        }
                    )
                except Exception as err:
                    errors.append(f"{table}.{record}: {err}")
        print("Finished updating database.")
        if errors:
            logger.get_logger().error(f"Some errors occured while updating database: \n {'\n'.join(errors)}")
        

def delete_table_records(db_manager: DatabaseManager):
    selected_table = single_select_input("Select table to remove records from", db_manager.get_db_tables())
    table_columns = db_manager.get_table_columns(selected_table)
    record_identifier = list(table_columns.keys())[0]

    record_ids = None
    # From file or query
    source_conditions = single_select_input("Select source for search conditions", ["Conditions Query","Identifier File"])
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
            user_selection = single_select_input("Select a Database Manager Action",[
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