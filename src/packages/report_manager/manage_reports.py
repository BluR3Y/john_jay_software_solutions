import os
import numpy as np
import pandas as pd

from modules.utils import request_user_selection, request_file_path, request_column_selection
from . import ReportGenerator
from packages.database_manager import DatabaseManager

PROCESS_NAME = "Report Manager"

def generate_reports(db_manager: DatabaseManager):
    with ReportGenerator(os.getenv('SAVE_PATH')) as report_generator:
        # Retrieve all the tables in the database
        db_tables = db_manager.get_db_tables()
        while True:
            try:
                if report_generator.get_num_reports():
                    selected_action = request_user_selection("Enter a next step:", ["Generate another report", "Save and Exit"])
                    if selected_action == "Save and Exit":
                        break
                    
                selected_table = request_user_selection("Enter the name of the table whose records will be used to populate the report:", db_tables)
                table_columns = db_manager.get_table_columns(selected_table).keys()
                record_identifier = table_columns[0]
                
                selected_search_conditions = input("WHERE: ")
                if not selected_search_conditions:
                    raise ValueError("Failed to provide query search conditions")
                
                formatted_search_conditions = db_manager.parse_sql_condition(selected_search_conditions)
                print(f"Developer Info: {formatted_search_conditions}")
                
                search_result = db_manager.select_query(
                    selected_table,
                    [record_identifier],
                    selected_search_conditions
                )
                record_ids = [item[record_identifier] for item in search_result]
                print(f"Search returned {len(record_ids)} records.")
                
                if record_ids:
                    selected_properties = request_column_selection(f"Input the columns in the '{selected_table}' table that will be used to populate the report.", table_columns)
                    # if not selected_properties:
                    #     raise ValueError("Failed to provide table columns.")
                    if record_identifier not in selected_properties:
                        selected_properties.insert(0, record_identifier)

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
            except ValueError as err:
                print(f"Validation Error: {err}")
            except Exception as err:
                print(f"An unexpected error occured: {err}")

def resolve_reports(db_manager: DatabaseManager):
    try:
        file_path = request_file_path("Enter the file path of the Excel file:", [".xlsx"])
        
        # Read the Excel file once
        report_data_frame = pd.read_excel(file_path, sheet_name=None)
        
        # Validate metadata presence
        if "report_meta_data" not in report_data_frame:
            raise KeyError("Report is missing metadata sheet.")
        
        # Load metadata
        meta_data_records = report_data_frame["report_meta_data"].to_dict(orient='records')
        meta_data = {record['sheet_name']: record for record in meta_data_records}
        
        # Process each sheet except metadata
        sheet_names = [s for s in report_data_frame.keys() if s != "report_meta_data"]
        
        for sheet_name in sheet_names:
            if sheet_name not in meta_data:
                # raise KeyError(f"Metadata does not include data regarding the sheet '{sheet_name}'")
                continue
            
            sheet_meta_data = meta_data[sheet_name]
            sheet_data_frame = report_data_frame[sheet_name]
            sheet_record_identifier = sheet_meta_data['record_identifier']
            sheet_columns = sheet_data_frame.columns.tolist()

            selected_properties = request_column_selection(f"Select columns for '{sheet_name}' (comma-separated) or leave black:", sheet_columns)
            if not selected_properties:
                continue  # Skip sheet if no columns selected
            
            # Ensure record identifier is included
            if sheet_record_identifier not in selected_properties:
                selected_properties.insert(0, sheet_record_identifier)

            # Validate column existence
            for prop in selected_properties:
                if prop not in sheet_columns:
                    raise ValueError(f"The column '{prop}' does not exist in the sheet '{sheet_name}'")

            # Filter and clean data
            filtered_data_frame = sheet_data_frame[selected_properties].replace({pd.NaT: None, np.nan: None})
            for col in filtered_data_frame.select_dtypes(include=["datetime64[ns]"]):
                filtered_data_frame[col] = filtered_data_frame[col].apply(lambda x: x.to_pydatetime() if pd.notnull(x) else None)
            sheet_rows = filtered_data_frame.to_dict(orient='records')

            for row in sheet_rows:
                record_id = row[sheet_record_identifier]
                db_manager.update_query(
                    sheet_meta_data['table'],
                    {name:val for name, val in row.items() if name != sheet_record_identifier},
                    {
                        sheet_record_identifier: {
                            "operator": "=",
                            "value": record_id
                        }
                    }
                )

        print("Finished making changes to records in the database.")

    except FileNotFoundError:
        print("Error: The specified file was not found.")
    except KeyError as err:
        print(f"Error: Missing key in metadata or sheet - {err}")
    except ValueError as err:
        print(f"Validation Error: {err}")
    except Exception as err:
        print(f"An unexpected error occurred: {err}")

def manage_reports(db_path: str):
    with DatabaseManager(db_path, PROCESS_NAME) as db_manager:
        print(f"Current Process: {PROCESS_NAME}")
        while True:
            user_selection = request_user_selection("Select a Report Manager Action:", ["Generate Reports", "Resolve Reports", "Exit Process"])

            if user_selection == "Generate Reports":
                generate_reports(db_manager)
            elif user_selection == "Resolve Reports":
                resolve_reports(db_manager)
            else:
                return