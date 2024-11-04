
import re
import pandas as pd
from methods import utils

SHEET_NAME = "Award - Template"

# Method that will populate the "Discipline" column in the Microsoft Access DB
# * Requires Excel document with the project's key (Prsy) and the discipline
def populate_db_discipline(self):
    # Request path to the file from the user
    file_path = utils.request_file_path("Enter the path of the file that will be used to populate the database", ['.xlsx'])
    # Read the contents of the file
    file_content = pd.read_excel(
        file_path,
        sheet_name="prsy_index_report",
        header=4    # Specifies the row to use as the column names
    )
    sheet_logger = dict()

    discipline_query = "SELECT Name FROM LU_Discipline;"
    result = self.execute_query(discipline_query)
    project_disciplines = { discipline["Name"]: {
        "primary_keys": []
    } for discipline in result}

    # Loop through every record in the table
    for index, row in file_content.iterrows():
        primary, secondary, tertiary = re.split(r'[-\s]+', row['Prsy'])
        rf_id = primary+secondary

        discipline = row.get("Discipline", None)
        # Checks if the 'Discipline' value is missing
        if not pd.isna(discipline):
            # Regex expression checks if discipline has an abbreviation
            regex_match = re.search(r'-\s*(.+)', discipline)
            # If so, the discipline is extracted from the string
            if regex_match:
                discipline = regex_match.group(1)
            else:
                sheet_logger[f"{primary}-{secondary}-{tertiary}"] = f"The value '{discipline}' for the Discipline of the Project is unusually formatted"
        else:
            discipline = None
            sheet_logger[f"{primary}-{secondary}-{tertiary}"] = "Project is missing Discipline value in the imported file."
            continue

        correlating_item = None
        for key in project_disciplines:
            if key.lower() == discipline.lower():
                correlating_item = key
                break
        if (correlating_item):
            if rf_id not in project_disciplines[correlating_item]["primary_keys"]:
                project_disciplines[correlating_item]["primary_keys"].append(rf_id)
        else:
            sheet_logger[f"{primary}-{secondary}-{tertiary}"] = f"Project has the value '{discipline}' for it's Discipline field in the imported file, which is an invalid value."

    for index, key in enumerate(project_disciplines):
        if project_disciplines[key]["primary_keys"]:
            primary_keys = set(project_disciplines[key]["primary_keys"])
            verify_query = f"""
                SELECT RF_Account
                FROM grants
                WHERE RF_Account IN ({','.join(['?' for _ in primary_keys])})
            """
            verify_result = self.execute_query(verify_query, *primary_keys)
            existing_keys = set([key['RF_Account'] for key in verify_result])
            if existing_keys:
                update_query = f"""
                    UPDATE grants
                    SET Discipline = ?
                    WHERE RF_Account IN ({','.join(['?' for _ in existing_keys])})
                """
                self.execute_query(update_query, key, *existing_keys)
            
            missing_keys = primary_keys - existing_keys
            for key in missing_keys:
                sheet_logger[f"{key}:database"] = "No record exists in the database with the RF_Account"
            
        print(f"Process is {round(index/len(project_disciplines) * 100)}% complete")

    self.append_process_logs(SHEET_NAME, {
        "populate_db_discipline": {
        "description": "Process processes data from an excel file, which should contain a table with the RF_Account and discipline of the awards, and updates the 'Discipline' field of the records in the Microsoft Access database. Additionally, the process also catches various types of issues found in the data from multiple sources such as the imported file and the database and logs them.",
        "logs": sheet_logger
    } })

def populate_template_discipline(self):
    sheet_logger = dict()
    # Retrieve the content of the proposal sheet
    award_sheet_content = self.df[SHEET_NAME]

    # Retrieve the disciplines from the table LU_Discipline in the database
    discipline_query = "SELECT Name FROM LU_Discipline;"
    discipline_result = self.execute_query(discipline_query)
    valid_disciplines = [value['Name'] for value in discipline_result]

    last_index = 0
    batch_limit = 40
    num_sheet_rows = len(award_sheet_content)
    # Loop while index has not reached the number of rows in the sheet
    while last_index < num_sheet_rows:
        new_end = last_index + batch_limit
        batch_ids = award_sheet_content['proposalLegacyNumber'][last_index:new_end].tolist()
        last_index = new_end    
    
        # Retrieve the Grant_ID and Discipline value of the records in the batch_ids list
        search_query = f"SELECT Grant_ID, Discipline FROM grants WHERE Grant_ID IN ({','.join(['?' for _ in batch_ids])})"
        search_result = self.execute_query(search_query, batch_ids)
        project_disciplines = { project['Grant_ID']:project['Discipline'] for project in search_result }

        # Loop through every grant_id in the batch
        for index, id in enumerate(batch_ids):
            document_index = last_index - batch_limit + index
            # Check if the database returned a record with the id
            if id in project_disciplines:
                # Check that the database did not return an empty value for the department of the current record
                if project_disciplines[id]:
                    # Validate that the discipline value of the record in the database is valid
                    if project_disciplines[id] in valid_disciplines:
                        item_discipline = award_sheet_content['Discipline'][document_index]
                        if pd.isna(item_discipline):
                            award_sheet_content.loc[document_index, 'Discipline'] = project_disciplines[id]
                        else:
                            if item_discipline != project_disciplines[id]:
                                self.append_cell_comment(
                                    SHEET_NAME,
                                    document_index + 1,
                                    award_sheet_content.columns.get_loc('Discipline'),
                                    f"The record has the value '{project_disciplines[id]}' assigned to it's discipline in the database."
                                )
                    else:
                        log = f"The record has '{project_disciplines[id]}' for the discipline in the database which may be invalid."
                        closest_match = utils.find_closest_match(project_disciplines[id], [dept for dept in valid_disciplines])
                        if closest_match:
                            log += " Did you possibly mean to assign: " + closest_match
                        # else:
                        #     missing_departments.add(project_departments[id])
                        self.append_cell_comment(
                            SHEET_NAME,
                            document_index + 1,
                            award_sheet_content.columns.get_loc('Discipline'),
                            log
                        )
                else:
                    self.append_cell_comment(
                        SHEET_NAME,
                        document_index + 1,
                        award_sheet_content.columns.get_loc('Discipline'),
                        "The record does not have a value assigned for the discipline in the database."
                    )
            else:
                self.append_cell_comment(
                    SHEET_NAME,
                    document_index + 1,
                    award_sheet_content.columns.get_loc('proposalLegacyNumber'),
                    f"Id {id} is not associated with any record in the database."
                )

        print(f"Process is {round(last_index/num_sheet_rows * 100)}% complete")
            
    self.append_process_logs(SHEET_NAME, {
        "populate_template_discipline": {
            "description": "Process populates the 'Discipline' column of the awards in the template document with the value the record is assigned in the Microsoft Access database. Additionally, the process also catches various types of issues found in the data from multiple sources such as the template file and the database and logs them.",
            "logs": sheet_logger
        }
    })

def populate_template_department(self):
    # ------------------------- LU_Department table is polluted with invalid values (Approach is currently unusable) ------------------------------
    # # Retrieve the departments from the table LU_Department in the database
    # department_query = "SELECT LU_Department AS Name FROM LU_Department"
    # department_result = self.execute_query(department_query)
    # valid_departments = [value['Name'] for value in department_result]
    # ---------------------------------------------------------------------------------------------------------------------------------------------

    # --------------------------------------- Request file with valid departments (Alternative approach) ------------------------------------------
    file_path = utils.request_file_path("Enter the path of the file with the valid Departments", ['.xlsx'])
    # Read the contents of the file
    file_content = pd.read_excel(file_path)
    # valid_departments = [ dept.split(" - ")[1] for dept in file_content['Name'] ]
    valid_departments = { dept['Name'].split(" - ")[1]: dept['Primary Code'] for index, dept in file_content.iterrows() }
    missing_departments = set()
    # ---------------------------------------------------------------------------------------------------------------------------------------------

    sheet_logger = dict()
    # Retrieve the content of the proposal sheet
    proposal_sheet_content = self.df[SHEET_NAME]

    last_index = 0
    batch_limit = 40
    num_sheet_rows = len(proposal_sheet_content)
    # Loop while index has not reached the number of rows in the sheet
    while last_index < num_sheet_rows:
        new_end = last_index + batch_limit
        batch_ids = proposal_sheet_content['proposalLegacyNumber'][last_index:new_end].tolist()
        last_index = new_end

        # Retrieve the Grant_ID and the Primary_Dept value of the records in the batch_ids list
        search_query = f"""
            SELECT Grant_ID, Primary_Dept
            FROM grants
            WHERE Grant_ID IN ({','.join(['?' for _ in batch_ids])})
        """
        search_result = self.execute_query(search_query, batch_ids)
        project_departments = { project['Grant_ID']:project['Primary_Dept'] for project in search_result }

        # Loop through every grant_id in the batch
        for index, id in enumerate(batch_ids):
            document_index = last_index - batch_limit + index
            # Check if the database returned a record with the id
            if id in project_departments:
                # Check that the database did not return an empty value for the department of the current record
                if project_departments[id]:
                    # Validate that the department value of the record in the database is valid
                    if project_departments[id] in valid_departments:
                        item_dept = proposal_sheet_content['Admin Unit'][document_index]
                        if pd.isna(item_dept):
                            # Assign the 'Admin Unit' property of the row with the id the updated value
                            proposal_sheet_content.loc[document_index, 'Admin Unit'] = project_departments[id]
                            # Assign the 'Admin Unit Primary Code' property of the row with the id the updated value
                            proposal_sheet_content.loc[document_index, 'Admin Unit Primary Code'] = valid_departments[project_departments[id]]
                        else:
                            if item_dept == project_departments[id]:
                                # Assign the 'Admin Unit Primary Code' property of the row with the id the updated value
                                proposal_sheet_content.loc[document_index, 'Admin Unit Primary Code'] = valid_departments[item_dept]
                            else:
                                if item_dept not in valid_departments:
                                    proposal_sheet_content.loc[document_index, 'Admin Unit'] = project_departments[id]
                                    proposal_sheet_content.loc[document_index, 'Admin Unit Primary Code'] = valid_departments[project_departments[id]]
                                    sheet_logger[f"{id}:department"] = f"The value '{item_dept}' for the department of the record was updated to '{project_departments[id]}'. This is because the previous value was not a valid department."
                                else:
                                    self.append_cell_comment(
                                        SHEET_NAME,
                                        document_index + 1,
                                        proposal_sheet_content.columns.get_loc('Admin Unit'),
                                        f"The record has the value '{project_departments[id]}' assigned to it's department in the database."
                                    )
                    else:
                        log = f"The record has '{project_departments[id]}' for the department in the database which may be invalid."
                        closest_match = utils.find_closest_match(project_departments[id], [dept for dept in valid_departments])
                        if closest_match:
                            log += " Did you possibly mean to assign: " + closest_match
                        else:
                            missing_departments.add(project_departments[id])
                        self.append_cell_comment(
                            SHEET_NAME,
                            document_index + 1,
                            proposal_sheet_content.columns.get_loc('Admin Unit'),
                            log
                        )
                else:
                    self.append_cell_comment(
                        SHEET_NAME,
                        document_index + 1,
                        proposal_sheet_content.columns.get_loc('Admin Unit'),
                        "The record does not have a value assigned for the department in the database."
                    )
            else:
                self.append_cell_comment(
                    SHEET_NAME,
                    document_index + 1,
                    proposal_sheet_content.columns.get_loc('proposalLegacyNumber'),
                    f"Id {id} is not associated with any record in the database."
                )
        print(f"Process is {round(last_index/num_sheet_rows * 100)}% complete")

    self.append_process_logs(SHEET_NAME, {
        "populate_template_department": {
            "description": "Process populates the 'Admin Unit' column of the proposals in the template document with the value the record is assigned in the Microsoft Access database. Additionally, the process also catches various types of issues found in the data from multiple sources such as the template file and the database and logs them.",
            "logs": sheet_logger,
            "missing_departments": list(missing_departments)
        }
    })