from classes.Process import Process
from methods import utils

import openpyxl
import os
import pandas as pd
import numpy as np

SHEET_NAME = "Other"

def database_record_modifier(self):
    process_name = "Modify Database Records"
    def logic():
        # Retrieve all the tables in the database
        tables = self.db_manager.get_db_tables()

        while True:
            selected_table = input("Enter the name of the table whose records you wish to alter: ")
            if selected_table in tables:
                table_columns = self.db_manager.get_table_columns(selected_table)
                record_identifier = table_columns[0]
                selected_search_conditions = input(f"Input the name of the column in the '{selected_table}' table followed by the value in the selected column separated by a ':' and enclosed in double quotes, which will be used to filter records in the database. Ex: \"Discipline:Philosophy\": ")
                search_conditions = dict()
                for condition in utils.extract_quoted_strings(selected_search_conditions):
                    col, val = condition.split(':')
                    if col in table_columns:
                        search_conditions[col] = val
                    else:
                        print(f"The column '{col}' does not exist in the table '{selected_table}'.")
                        break
                
                search_result = self.db_manager.select_query(
                    selected_table,
                    [record_identifier],
                    (' AND '.join([f"{col}=?" for col in search_conditions.keys()])),
                    *search_conditions.values()
                )
                record_ids = [item[record_identifier] for item in search_result]
                print(f"Search returned {len(record_ids)} records.")
                
                if record_ids:
                    selected_alter_properties = input(f"Input the name of the column in the '{selected_table}' table that will be updated followed by the new value separated by a ':' and enclosed in double quites. Ex: \"Discipline:Philosophy\": ")
                    alter_properties = dict()
                    for prop in utils.extract_quoted_strings(selected_alter_properties):
                        col, val = prop.split(':')
                        if col in table_columns:
                            alter_properties[col] = val
                        else:
                            print(f"The column '{col}' does not exist in the table '{selected_table}'")
                            break

                    self.db_manager.update_query(
                        process_name,
                        selected_table,
                        alter_properties,
                        f"{record_identifier} IN ({','.join(['?' for _ in record_ids])})",
                        *record_ids
                    )
            else:
                print(f"Table '{selected_table}' does not exist in the database.")

            user_decision = input("Would you like to continue with another update operation (y)es/(n)o: ")
            if not user_decision.startswith('y'):
                break

    return Process(
        logic,
        process_name,
        "This process provides an interactive tool for modifying records within a specified table in a connected database. It allows users to select a table, define search conditions, and update multiple records in a single operation. This function is designed for dynamic and secure interaction with the database, verifying that tables and columns exist before performing operations and using parameterized queries to avoid SQL injection risks. It encapsulates the entire process in a callable Process object, ready to be integrated into larger workflows or batch processes."
    )
    
def report_generator(self):
    process_name = "Generate Report"
    def logic():
        # Retrieve all the tables in the database
        tables = self.db_manager.get_db_tables()
        generated_reports = {}

        while True:
            try:
                if generated_reports:
                    selected_action = utils.request_user_selection("Enter a next step:", ["Generate another report", "Save and Exit"])
                    if selected_action == "Save and Exit":
                        break
                    
                selected_table = utils.request_user_selection("Enter the name of the table whose records will be used to populate the report:", tables)
                table_columns = self.db_manager.get_table_columns(selected_table)
                record_identifier = table_columns[0]
                
                selected_search_conditions = input("WHERE: ")
                if selected_search_conditions:
                    formatted_search_conditions = utils.parse_query_conditions(selected_search_conditions, table_columns)
                    print("Developer info: ", formatted_search_conditions)
                else:
                    raise Exception("Failed to provide query search conditions.")
                
                search_result = self.db_manager.select_query(
                    selected_table,
                    [record_identifier],
                    formatted_search_conditions
                )
                record_ids = [item[record_identifier] for item in search_result]
                print(f"Search returned {len(record_ids)} records.")
                
                if record_ids:
                    selected_properties_input = input(f"Input the name of the columns in the '{selected_table}' table that will be used to populate the report. \n The table has the columns: {", ".join(table_columns)} \n Selection: ")
                    selected_properties = selected_properties_input.split(' ')
                    for prop in selected_properties:
                        if prop not in table_columns:
                            print(f"The column '{prop}' does not exist in the table '{selected_table}'.")
                            break
                    if record_identifier not in selected_properties:
                        selected_properties.insert(0, record_identifier)
                        
                    last_index = 0
                    batch_limit = 40
                    report_data = []
                    while last_index < len(record_ids):
                        new_end = last_index + batch_limit
                        batch_ids = [str(item) for item in record_ids[last_index:new_end]]
                        last_index = new_end

                        search_result = self.db_manager.select_query(
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
                        
                    selected_report_name = input("What would you like to name this report? ")
                    if not selected_report_name:
                        raise Exception("Failed to provide a report name.")
                    
                    # generated_reports[selected_report_name] = pd.DataFrame(report_data)
                    generated_reports[selected_report_name] = {
                        "table": selected_table,
                        "record_identifier": record_identifier,
                        "search_condition": selected_search_conditions,
                        "formatted_search_condition": formatted_search_conditions,
                        "data_frame": pd.DataFrame(report_data),
                    }
            except Exception as e:
                print(e)

        if generated_reports:
            save_location = os.path.join(os.getenv("SAVE_PATH"), "generated_report.xlsx")
            # Use ExcelWriter to write multiple sheets into an Excel file
            with pd.ExcelWriter(save_location) as writer:
                report_meta_data = []
                meta_data_columns = ['sheet_name', 'table', 'record_identifier', 'search_condition', 'formatted_search_condition']
                
                for sheet_name, sheet_info in generated_reports.items():
                    df_sheet = sheet_info["data_frame"]
                    df_sheet.to_excel(writer, sheet_name=sheet_name, index=False)
                    report_meta_data.append([sheet_name, sheet_info['table'], sheet_info['search_condition'], sheet_info['formatted_search_condition']])
                
                # Create MetaData DataFrame
                meta_data_frame = pd.DataFrame(report_meta_data, columns=meta_data_columns)
                meta_data_frame.to_excel(writer, sheet_name="report_meta_data", index=False)
                
            # Load the report workbook
            report_workbook = openpyxl.load_workbook(save_location)
            # Set the state of the MetaData sheet to hidden
            report_workbook["report_meta_data"].sheet_state = "hidden"
            # Save the state change made to the workbook
            report_workbook.save(save_location)
                
            print(f"File saved to {save_location}")

    return Process(
        logic,
        process_name,
        ""
    )
    
def report_resolver(self):
    process_name = "Report Resolver"

    def logic():
        file_path = utils.request_file_path("Enter the file path of the excel file:", [".xlsx"])
        
        # Read the Excel file
        excel_file = pd.ExcelFile(file_path)
        # Get the sheet names
        sheet_names = excel_file.sheet_names
        if "report_meta_data" in sheet_names:
           sheet_names.remove("report_meta_data")
        else:
            raise Exception("Report is missing metadata sheet.")
        
        report_data_frame = pd.read_excel(file_path, sheet_name=None)
        meta_data_records = report_data_frame["report_meta_data"].to_dict(orient='records')
        meta_data = {record['sheet_name']: record for record in meta_data_records}

        for sheet_name in sheet_names:
            if not sheet_name in meta_data:
                raise Exception(f"Metadata does not include data regarding the sheet {sheet_name}")

            sheet_meta_data = meta_data[sheet_name]
            # sheet_data_frame = report_data_frame[sheet_name].to_dict(orient="records")
            sheet_data_frame = report_data_frame[sheet_name]
            sheet_data_frame.replace([pd.NaT, np.nan], None, inplace=True)
            
            sheet_rows = sheet_data_frame.to_dict(orient="records")
            sheet_record_identifier = sheet_meta_data['record_identifier']
            
            for sheet_row in sheet_rows:
                record_id = sheet_row[sheet_record_identifier]
                del sheet_row[sheet_record_identifier]
                self.db_manager.update_query(
                    process_name,
                    sheet_meta_data['table'],
                    sheet_row,
                    {
                        sheet_record_identifier: {
                            "operator": "=",
                            "value": record_id
                        }
                    }
                )
        print("Finished making changes to records in database.")
    return Process(
        logic,
        process_name,
        ""
    )    
    
    
def database_record_plc_populator(self):
    process_name = "Populate Database Record ProjectLegacyNumber"
    
    def logic():
        # Ensure column exists in the grants table
        if "Project_Legacy_Number" not in self.db_manager.get_table_columns("grants"):
            print("Creating table column...")
            self.db_manager.execute_query("ALTER TABLE grants ADD COLUMN project_legacy_number INTEGER;")

        # Fetch grants data and create a dictionary for quick lookup
        get_res = self.db_manager.execute_query("SELECT Grant_ID, Project_Legacy_Number FROM grants;")
        grants = {int(grant['Grant_ID']): (int(grant['Project_Legacy_Number']) if grant['Project_Legacy_Number'] is not None else None) for grant in get_res}

        # Load the relevant proposal data as a dictionary
        proposal_data_frame = self.template_manager.df["Proposal - Template"][['projectLegacyNumber', 'proposalLegacyNumber']]
        proposal_dict = {
            int(row['proposalLegacyNumber']): int(row['projectLegacyNumber'])
            for _, row in proposal_data_frame.astype({'projectLegacyNumber': int, 'proposalLegacyNumber': int}).iterrows()
        }

        # Initialize result lists
        existing_pln, missing_pln, conflicting_pln = [], [], []
        greatest_pln = max(
            max((pln for pln in grants.values() if pln is not None), default=float("-inf")),
            max(proposal_dict.values(), default=float("-inf"))
        )

        # Process grants and compare with proposals
        for grant_id, project_legacy_number in grants.items():
            proposal_project_legacy_number = proposal_dict.get(grant_id)
            if proposal_project_legacy_number:
                greatest_pln = max(greatest_pln, proposal_project_legacy_number)

            if project_legacy_number is None:
                # If the grant has no project legacy number, determine if it should be assigned
                if proposal_project_legacy_number:
                    existing_pln.append((proposal_project_legacy_number, grant_id))
                else:
                    missing_pln.append(grant_id)
            elif proposal_project_legacy_number and project_legacy_number != proposal_project_legacy_number:
                # If there's a mismatch between grant and proposal
                conflicting_pln.append(grant_id)

        # Handle conflicts
        if conflicting_pln:
            conflict_details = [
                f"Grant ID {grant_id}: expected {proposal_dict.get(grant_id)}, found {grants[grant_id]}"
                for grant_id in conflicting_pln
            ]
            raise Exception(f"Conflicts detected:\n" + "\n".join(conflict_details))

        # Assign missing project legacy numbers
        if missing_pln:
            next_pln = greatest_pln + 1
            for grant_id in missing_pln:
                existing_pln.append((next_pln, grant_id))
                next_pln += 1

        # Batch update the database
        if existing_pln:
            # Ensure all parameters are native Python types
            existing_pln = [(int(pln), int(grant_id)) for pln, grant_id in existing_pln]
            rows_updated = self.db_manager.execute_many_query(
                "UPDATE grants SET Project_Legacy_Number = ? WHERE Grant_ID = ?;", existing_pln
            )
            print(f"Updated {rows_updated} rows in the database.")
    return Process(
        logic,
        process_name,
        ""
    )
    
def database_discipline_repair(self):
    process_name = "Database Discipline Fixer"
    
    def logic():
        select_query = self.db_manager.execute_query("SELECT * FROM LU_Discipline")
        valid_disciplines = {int(item['ID']):item['Name'] for item in select_query}
        invalid_grants = {}
        
        query_grants = self.db_manager.execute_query("SELECT Grant_ID, Discipline FROM grants")
        grants = {int(grant['Grant_ID']): grant['Discipline'] for grant in query_grants}
        
        for grant_id, grant_discipline in grants.items():
            if not grant_discipline:
                print(f"Grant {grant_id} doesnt have a discapline")
                continue
            
            if grant_discipline.isnumeric():
                numeric_discipline = int(grant_discipline)
                if numeric_discipline in invalid_grants:
                    invalid_grants[numeric_discipline].append(grant_id)
                else:
                    invalid_grants[numeric_discipline] = [grant_id]

        for discipline_id, grants in invalid_grants.items():
            if discipline_id in valid_disciplines:
                discipline_name = valid_disciplines[discipline_id]
                
                batch_limit = 40
                num_grants = len(grants)
                last_index = 0
                while last_index < num_grants:
                    new_end = last_index + batch_limit
                    batch_ids = grants[last_index:new_end]
                    last_index = new_end
                    
                    update_query = f"UPDATE grants SET Discipline = ? WHERE Grant_ID IN ({','.join('?' for _ in batch_ids)})"
                    self.db_manager.cursor.execute(update_query, discipline_name, *batch_ids)
                    self.db_manager.connection.commit()
            else:
                print(f"No valid discipline associated with: {discipline_id}")
    
    return Process(
        logic,
        process_name,
        ""
    )
    
def database_award_type_repair(self):
    process_name = "Database Award Type Fixer"
    
    def logic():
        select_query = self.db_manager.execute_query("SELECT ID, Field1 FROM LU_AType")
        valid_types = {int(item['ID']):item['Field1'] for item in select_query}
        invalid_types = {}
    
        query_grants = self.db_manager.execute_query('SELECT Grant_ID, "Award Type" FROM grants')
        grants = {int(grant['Grant_ID']): grant['Award Type'] for grant in query_grants}
    
        for grant_id, award_type in grants.items():
            if not award_type:
                continue
            
            if award_type.isnumeric():
                numeric_type = int(award_type)
                if numeric_type in invalid_types:
                    invalid_types[numeric_type].append(grant_id)
                else:
                    invalid_types[numeric_type] = [grant_id]
        
        for award_id, grants in invalid_types.items():
            if award_id in valid_types:
                type_name = valid_types[award_id]
                
                batch_limit = 40
                num_grants = len(grants)
                last_index = 0
                while last_index < num_grants:
                    new_end = last_index + batch_limit
                    batch_ids = grants[last_index:new_end]
                    last_index = new_end
                    
                    update_query = f'UPDATE grants SET "Award Type" = ? WHERE Grant_ID IN ({','.join('?' for _ in batch_ids)})'
                    self.db_manager.cursor.execute(update_query, type_name, *batch_ids)
                    self.db_manager.connection.commit()
            else:
                print(f"No valid Award Type associated with: {award_id}")
    
    return Process(
        logic,
        process_name,
        ""
    )