import os

from modules.utils import request_user_selection
from . import ReportGenerator
from packages.database_manager import DatabaseManager

def generate_reports(db_manager: DatabaseManager):
    with ReportGenerator(os.getenv('SAVE_PATH')) as report_generator:
        # Retrieve all the tables in the database
        db_tables = db_manager.get_db_tables()
        while True:
            try:
                if report_generator.generated_reports:
                    selected_action = request_user_selection("Enter a next step:", ["Generate another report", "Save and Exit"])
                    if selected_action == "Save and Exit":
                        break
                    
                selected_table = request_user_selection("Enter the name of the table whose records will be used to populate the report:", db_tables)
                table_columns = db_manager.get_table_columns(selected_table)
                record_identifier = table_columns[0]
                
                selected_search_conditions = input("WHERE: ")
                if not selected_search_conditions:
                    raise ValueError("Failed to provide query search conditions")
                
                formatted_search_conditions = report_generator.parse_query_conditions(selected_search_conditions, table_columns)
                print(f"Developer Info: {formatted_search_conditions}")
                
                search_result = db_manager.select_query(
                    selected_table,
                    [record_identifier],
                    formatted_search_conditions
                )
                record_ids = [item[record_identifier] for item in search_result]
                print(f"Search returned {len(record_ids)} records.")
                
                if record_ids:
                    selected_properties_input = input(f"Input the name of the columns in the '{selected_table}' table that will be used to populate the report. \n The table has the columns: {", ".join(table_columns)} \n Selection: ")
                    selected_properties = selected_properties_input.split(' ')
                    if not selected_properties:
                        raise ValueError("Failed to provide table columns.")
                    if record_identifier not in selected_properties:
                        selected_properties.insert(0, record_identifier)
                    
                    for prop in selected_properties:
                        if prop not in table_columns:
                            raise ValueError(f"The column '{prop}' does not exist in the table '{selected_table}'")

                    last_index = 0
                    batch_limit = 40
                    report_data = []
                    while last_index < len(record_ids):
                        new_end = last_index + batch_limit
                        batch_ids = [str(item) for item in record_ids[last_index:new_end]]
                        last_index = new_end

                        search_result = db_manager.select_query(
                            selected_table,
                            selected_properties,
                            {
                                record_identifier: {
                                    "operator": "IN",
                                    "value": batch_ids
                                }
                            }
                        )
                        report_data.extend(search_result)
                        
                    selected_report_name = input("What would you like to name this report: ")
                    if not selected_report_name:
                        raise ValueError("Failed to provide a report name.")
                    
                    report_generator.append_report(selected_report_name, selected_table, record_identifier, report_data)
            except Exception as err:
                print(err)

def resolve_reports(db_manager: DatabaseManager):
    pass

def manage_reports(db_manager: DatabaseManager):
    print("Current Process: Report Manager")
    while True:
        user_selection = request_user_selection("Select a Report Manager Action:", ["Generate Reports", "Manage Reports", "Exit Process"])
        
        if user_selection == "Generate Reports":
            generate_reports(db_manager)
        elif user_selection == "Resolve Reports":
            resolve_reports(db_manager)
        else:
            return