from pathlib import Path
import os
from datetime import datetime

from ..packages.database_manager import DatabaseManager
from ..packages.workbook_manager import WorkbookManager
from ..modules.utils import request_file_path, multi_select_input, single_select_input


def generate_reports(db_manager: DatabaseManager):
    with WorkbookManager(write_file_path=Path(os.getenv("SAVE_PATH")) / f"generated_report_{datetime.now().strftime("%Y_%m_%d")}.xlsx") as report_workbook:
        report_meta = report_workbook.create_sheet("report_meta_data", ["sheet_name", "table", "record_identifier"])
        report_meta.assigned_sheet_props["sheet_state"] = "hidden"
        # Retrieve all the tables in the database
        db_tables = db_manager.get_db_tables()
        while True:
            try:
                if report_meta.df.shape[0]:
                    selected_action = single_select_input("Enter a next step", ["Generate another report.", "Save and Exit"])
                    if selected_action == "Save and Exit":
                        break
                
                selected_table = single_select_input("Enter the name of the table whose records will be used to populate the report", db_tables)
                table_columns = list(db_manager.get_table_columns(selected_table).keys())
                record_identifier = table_columns[0]
                
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

                if record_ids:
                    selected_properties = multi_select_input(f"Input the columns in the '{selected_table}' table that will be used to populate the report.", table_columns)
                    if not selected_properties:
                        raise ValueError("Failed to provide table columns.")
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
                    report_workbook[selected_report_name] = report_data
                    query_condition = search_query if source_conditions == "Conditions Query" else str({record_identifier:{"operator":"IN","value":record_ids}})
                    report_meta.append_row({
                        "sheet_name": selected_report_name,
                        "table": selected_table,
                        "record_identifier": record_identifier,
                        "search_query": query_condition
                    })
            except ValueError as err:
                print(f"Validation Error: {err}")
            except Exception as err:
                print(f"An unexpected error occured: {err}")
        selected_wb_name = input("Select a file name for the report(Optional): ")
        if selected_wb_name:
            report_workbook.set_write_path(Path(os.getenv("SAVE_PATH")) / f"{selected_wb_name}.xlsx")

def resolve_reports(db_manager: DatabaseManager):
    try:
        file_path = request_file_path("Enter the file path of the Excel file:", [".xlsx"])
        # Create a workbook for the Excel file
        report_wb = WorkbookManager(file_path).__enter__()

        # Validate metadata presence
        report_meta = report_wb["report_meta_data"]
        if not report_meta:
            raise FileExistsError("Report is missing metadata")
        
        for sheet_meta in report_meta:
            record_identifier = sheet_meta.get('record_identifier')
            sheet_name = sheet_meta.get('sheet_name')
            sheet_manager = report_wb[sheet_name]
            sheet_columns = list(sheet_manager.get_df().keys())

            selected_properties = multi_select_input(f"Select columns for '{sheet_name}' (comma-separated) or leave blank:", sheet_columns)
            if not selected_properties:
                continue    # Skip sheet if no columns selected

            # Ensure record identifier is included
            if record_identifier not in selected_properties:
                selected_properties.insert(0, record_identifier)
            
            for row in report_wb[sheet_name].get_df(cols=selected_properties, format=True).to_dict(orient='records'):
                record_id = row[record_identifier]
                db_manager.update_query(
                    sheet_meta['table'],
                    {name:val for name, val in row.items() if name != record_identifier},
                    {
                        record_identifier: {
                            "operator": "=",
                            "value": record_id
                        }
                    }
                )
            print("Finished making changes to records in the database.")
    except FileNotFoundError as err:
        print(f"File Error: {err}")
    except KeyError as err:
        print(f"Key Error: {err}")
    except ValueError as err:
        print(f"Value Error: {err}")
    except Exception as err:
        print(f"An unexpected error occured: {err}")

def manage_reports():
    with DatabaseManager(os.getenv("ACCESS_DB_PATH"), "REPORT-MANAGER") as db_manager:
        while True:
            user_selection = single_select_input("Select a Report Manager Action", ["Generate Reports", "Resolve Reports", "Exit Process"])

            match user_selection:
                case "Generate Reports":
                    generate_reports(db_manager)
                case "Resolve Reports":
                    resolve_reports(db_manager)
                case _:
                    return