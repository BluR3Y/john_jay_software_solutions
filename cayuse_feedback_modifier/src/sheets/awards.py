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
                sheet_logger[f"{primary}-{secondary}-{tertiary}"] = "Project is assigned an unusual 'Discipline' value in the imported file."
        else:
            discipline = None
            sheet_logger[f"{primary}-{secondary}-{tertiary}"] = "Project is missing 'Discipline' value in the imported file."
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
                sheet_logger[f"{key}:database"] = "Record does not exist in the database."
            
        print(f"Database modifications are {round(index/len(project_disciplines) * 100)}% complete")

    self.append_process_logs(SHEET_NAME, {
        "populate_db_discipline": {
        "description": "Process processes data from an excel file, which should contain a table with the RF_Account and discipline of the awards, and updates the 'Discipline' field of the records in the Microsoft Access database. Additionally, the process also catches various types of issues found in the data from multiple sources such as the imported file and the database and logs them.",
        "logs": sheet_logger
    } })

def populate_template_discipline(self):
    award_sheet_content = self.df[SHEET_NAME]
    # Acquire all the rf_ids from the award sheet in the excel file
    award_query_ids = award_sheet_content['proposalLegacyNumber'].tolist()
    sheet_logger = dict()
    
    last_index = 0
    # Loop while index has not reached the length of the list
    while last_index <= len(award_query_ids):
        # The new end index will be the previous value plus 40, i.e, the limit of the list that will store the ids
        new_end = last_index + 40
        batch_ids = award_query_ids[last_index:new_end]
        # Assign the value of last_index to be that of new_end
        last_index = new_end
        
        # Retrieve the Grant_ID and Discipline value of the records in the batch_ids list
        search_query = f"SELECT Grant_ID, Discipline FROM grants WHERE Grant_ID IN ({','.join(['?' for _ in batch_ids])})"
        search_result = self.execute_query(search_query, batch_ids)
        project_disciplines = { project['Grant_ID']:project['Discipline'] for project in search_result }

        # Retrieve the disciplines from the table LU_Discipline in the database
        discipline_query = "SELECT Name FROM LU_Discipline;"
        discipline_result = self.execute_query(discipline_query)
        valid_disciplines = [value['Name'] for value in discipline_result]

        # Loop through every rf_id in the batch
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
                        sheet_logger[f"{id}:discipline"] = "The record's 'Discipline' value may be invalid"
                else:
                    sheet_logger[f"{id}:discipline"] = "The record does not have a value assigned for the 'Discipline' column"
            else:
                sheet_logger[f"{id}:database"] = "RF_Account is not associated with any record in the database."

    self.append_process_logs(SHEET_NAME, {
        "populate_template_discipline": {
            "description": "Process populates the 'Discipline' column of the awards in the template document with the value the record is assigned in the Microsoft Access database. Additionally, the process also catches various types of issues found in the data from multiple sources such as the template file and the database and logs them.",
            "logs": sheet_logger
        }
    })