import utils
import re
import pandas as pd

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
    # Retrieve the content of the awards sheet
    award_sheet_content = self.df[SHEET_NAME]
    # Acquire all the rf_ids from the award sheet in the excel file
    award_query_ids = award_sheet_content['proposalLegacyNumber'].tolist()
    sheet_logger = dict()

    # Retrieve the disciplines from the table LU_Discipline in the database
    discipline_query = "SELECT Name FROM LU_Discipline;"
    discipline_result = self.execute_query(discipline_query)
    valid_disciplines = [value['Name'] for value in discipline_result]
    
    last_index = 0
    batch_limit = 40
    # Loop while index has not reached the length of the list
    while last_index <= len(award_query_ids):
        # The new end index will be the previous value plus 40, i.e, the limit of the list that will store the ids
        new_end = last_index + batch_limit
        batch_ids = award_query_ids[last_index:new_end]
        # Assign the value of last_index to be that of new_end
        last_index = new_end
        
        # Retrieve the Grant_ID and Discipline value of the records in the batch_ids list
        search_query = f"SELECT Grant_ID, Discipline FROM grants WHERE Grant_ID IN ({','.join(['?' for _ in batch_ids])})"
        search_result = self.execute_query(search_query, batch_ids)
        project_disciplines = { project['Grant_ID']:project['Discipline'] for project in search_result }

        # Loop through every grant_id in the batch
        for id in batch_ids:
            # Check if the database returned a record with the id
            if id in project_disciplines:
                # If the 'Discipline' field for the record in the database is not empty
                if project_disciplines[id]:
                    # Validate that the 'Discipline' value for the record in the database is a valid value
                    if project_disciplines[id] in valid_disciplines:
                        # Retrieve the index of the row with the id in the template file
                        file_record_index = award_sheet_content.index[award_sheet_content['proposalLegacyNumber'] == id]
                        # Assign the 'Discipline' property of the row with the id the updated value
                        award_sheet_content.loc[file_record_index, 'Discipline'] = project_disciplines[id]
                    else:
                        sheet_logger[f"{id}:discipline"] = f"The value '{project_disciplines[id]}' for the Discipline of the record may be invalid."
                else:
                    sheet_logger[f"{id}:discipline"] = "The record does not have a value assigned for the 'Discipline' column."
            else:
                sheet_logger[f"{id}:database"] = "Id is not associated with any record in the database."
        
        print(f"Process is {round(last_index/len(award_query_ids) * 100)}% complete")

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
    valid_departments = [ dept.split(" - ")[1] for dept in file_content['Name'] ]
    missing_departments = set()
    # ---------------------------------------------------------------------------------------------------------------------------------------------

    sheet_logger = dict()
    # Retrieve the content of the proposals sheet
    proposal_sheet_content = self.df[SHEET_NAME]
    # Acquire all the rf_ids from the award sheet in the excel file
    proposal_query_ids = proposal_sheet_content['proposalLegacyNumber'].tolist()

    last_index = 0
    batch_limit = 40
    # Loop while index has not reached the length of the list
    while last_index <= len(proposal_query_ids):
        # The new end index will be the previous value plus 40, i.e, the limit of the list that will store the ids
        new_end = last_index + batch_limit
        batch_ids = proposal_query_ids[last_index:new_end]
        # Assign the value of last_index to be that of new_end
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
        for id in batch_ids:
            # Check if the database returned a record with the id
            if id in project_departments:
                # Check that the database did not return an empty value for the department of the current record
                if project_departments[id]:
                    if project_departments[id] in valid_departments:
                        # Retrieve the index of the row with the current id in the template file
                        file_record_index = proposal_sheet_content.index[proposal_sheet_content['proposalLegacyNumber'] == id]
                        # Assign the 'Department' property of the row with the id the updated value
                        proposal_sheet_content.loc[file_record_index, 'Admin Unit'] = project_departments[id]
                    else:
                        closest_match = utils.find_closest_match(project_departments[id], valid_departments)
                        log = f"The value '{project_departments[id]}' for the department of the record may be invalid."
                        if closest_match:
                            log += " Did you possibly mean to assign: " + closest_match
                        else:
                            missing_departments.add(project_departments[id])
                        sheet_logger[f"{id}:department"] = log
                else:
                    sheet_logger[f"{id}:department"] = "The record does not have a value assigned for the department column"
            else:
                sheet_logger[f"{id}:database"] = "Id is not associated with any record in the database."

        print(f"Process is {round(last_index/len(proposal_query_ids) * 100)}% complete")

    self.append_process_logs(SHEET_NAME, {
        "populate_template_department": {
            "description": "Process populates the 'Admin Unit' column of the awards in the template document with the value the record is assigned in the Microsoft Access database. Additionally, the process also catches various types of issues found in the data from multiple sources such as the template file and the database and logs them.",
            "logs": sheet_logger,
            "missing_departments": list(missing_departments)
        }
    })

    
    
# ----------------- LU_Discipline table is polluted with invalid values (temporarily ususable)--------------------------
# def populate_template_department(self):
#     # Retrieve the content of the proposals sheet
#     proposal_sheet_content = self.df[SHEET_NAME]
#     # Acquire all the rf_ids from the award sheet in the excel file
#     proposal_query_ids = proposal_sheet_content['proposalLegacyNumber'].tolist()
#     sheet_logger = dict()

#     # Retrieve the departments from the table LU_Department in the database
#     department_query = "SELECT LU_Department AS Name FROM LU_Department"
#     department_result = self.execute_query(department_query)
#     valid_departments = [value['Name'] for value in department_result]

#     last_index = 0
#     batch_limit = 40
#     # Loop while index has not reached the length of the list
#     while last_index <= len(proposal_query_ids):
#         # The new end index will be the previous value plus 40, i.e, the limit of the list that will store the ids
#         new_end = last_index + batch_limit
#         batch_ids = proposal_query_ids[last_index:new_end]
#         # Assign the value of last_index to be that of new_end
#         last_index = new_end

#         # Retrieve the Grant_ID and the Primary_Dept value of the records in the batch_ids list
#         search_query = f"""
#             SELECT Grant_ID, Primary_Dept
#             FROM grants
#             WHERE Grant_ID IN ({','.join(['?' for _ in batch_ids])})
#         """
#         search_result = self.execute_query(search_query, batch_ids)
#         project_departments = { project['Grant_ID']:project['Primary_Dept'] for project in search_result }

#         # Loop through every grant_id in the batch
#         for id in batch_ids:
#             # Check if the database returned a record with the id
#             if id in project_departments:
#                 # Check that the database did not return an empty value for the department of the current record
#                 if project_departments[id]:
#                     if project_departments[id] in valid_departments:
#                         # Retrieve the index of the row with the current id in the template file
#                         file_record_index = proposal_sheet_content.index[proposal_sheet_content['proposalLegacyNumber'] == id]
#                         # Assign the 'Department' property of the row with the id the updated value
#                         proposal_sheet_content.loc[file_record_index, 'Admin Unit'] = project_departments[id]
#                     else:
#                         sheet_logger[f"{id}:department"] = f"The value '{project_departments[id]}' for the department of the record may be invalid."
#                 else:
#                     sheet_logger[f"{id}:department"] = "The record does not have a value assigned for the department column"
#             else:
#                 sheet_logger[f"{id}:database"] = "Id is not associated with any record in the database."

#         print(f"Process is {round(last_index/len(proposal_query_ids) * 100)}% complete")

#     self.append_process_logs(SHEET_NAME, {
#         "populate_template_department": {
#             "description": "Process populates the 'Admin Unit' column of the awards in the template document with the value the record is assigned in the Microsoft Access database. Additionally, the process also catches various types of issues found in the data from multiple sources such as the template file and the database and logs them.",
#             "logs": sheet_logger
#         }
#     })