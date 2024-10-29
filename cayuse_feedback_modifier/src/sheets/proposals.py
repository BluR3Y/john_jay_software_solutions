import utils
import pandas as pd

SHEET_NAME = "Proposal - Template"

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
    # Modify to pull id in addition to name

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
            "description": "Process populates the 'Admin Unit' column of the proposals in the template document with the value the record is assigned in the Microsoft Access database. Additionally, the process also catches various types of issues found in the data from multiple sources such as the template file and the database and logs them.",
            "logs": sheet_logger,
            "missing_departments": list(missing_departments)
        }
    })