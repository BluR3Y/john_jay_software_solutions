
import re
import pandas as pd
from methods import utils
from classes.Process import Process

SHEET_NAME = "Award - Template"

# *** Logging needs to be updated
def populate_db_discipline(self):
    process_name = 'Populate Database Disciplines'
    def logic():
        # Request path to the file from the user
        file_path = utils.request_file_path("Enter the path of the file that will be used to populate the database", ['.xlsx'])
        # Read the contents of the file
        file_content = pd.read_excel(
            file_path,
            sheet_name="prsy_index_report",
            header=4    # Specifies the row to use as the column names
        )
        sheet_logger = dict()

        result = self.db_manager.select_query(
            "LU_Discipline",
            ["Name"],
        )
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
                verify_result = self.db_manager.select_query(
                    "grants",
                    ["RF_Account"],
                    f"RF_Account IN ({','.join(['?' for _ in primary_keys])})",
                    *primary_keys
                )
                existing_keys = set([key['RF_Account'] for key in verify_result])
                if existing_keys:
                    self.db_manager.update_query(
                        process_name,
                        "grants",
                        {"Discipline":key},
                        f"RF_Account IN ({','.join(['?' for _ in existing_keys])})",
                        *existing_keys
                    )
                
                missing_keys = primary_keys - existing_keys
                for key in missing_keys:
                    sheet_logger[f"{key}:database"] = "No record exists in the database with the RF_Account"
                
            print(f"Process is {round(index/len(project_disciplines) * 100)}% complete")
        
        # if sheet_logger:
        #     self.log_manager.append_logs(SHEET_NAME, process_name, sheet_logger)
    return Process(
        logic,
        process_name,
        "This process processes data from an excel file, which should contain a table with the RF_Account and discipline of the awards, and updates the 'Discipline' field of the records in the Microsoft Access database. Additionally, the process also catches various types of issues found in the data from multiple sources such as the imported file and the database and logs them."
    )

def populate_template_discipline(self):
    process_name = 'Populate Template Disciplines'
    def logic():
        # Retrieve the content of the proposal sheet
        proposal_sheet_content = self.template_manager.df[SHEET_NAME]

        # Retrieve the disciplines from the table LU_Discipline in the database
        discipline_result = self.db_manager.select_query(
            "LU_Discipline",
            ["Name"]
        )
        valid_disciplines = [value['Name'] for value in discipline_result]

        last_index = 0
        batch_limit = 40
        num_sheet_rows = len(proposal_sheet_content)
        # Loop while index has not reached the number of rows in the sheet
        while last_index < num_sheet_rows:
            new_end = last_index + batch_limit
            batch_records = proposal_sheet_content.iloc[last_index:new_end]
            last_index = new_end

            batch_ids = batch_records['proposalLegacyNumber']
            search_result = self.db_manager.select_query(
                "grants",
                ["Grant_ID","Discipline"],
                f"Grant_ID IN ({','.join(['?' for _ in batch_ids])})",
                *batch_ids
            )
            project_disciplines = { project['Grant_ID']:project['Discipline'] for project in search_result }

            for document_index, record in batch_records.iterrows():
                record_grant_id = record['proposalLegacyNumber']

                # Check if the database returned a record with the id
                if record_grant_id in project_disciplines:
                    if project_disciplines[record_grant_id] and project_disciplines[record_grant_id] not in valid_disciplines:
                        closest_valid_discipline = utils.find_closest_match(project_disciplines[record_grant_id], valid_disciplines)
                        if closest_valid_discipline:
                            self.db_manager.update_query(
                                process_name,
                                SHEET_NAME,
                                {"Discipline":closest_valid_discipline},
                                "Grant_ID = ?",
                                record_grant_id
                            )
                            project_disciplines[record_grant_id] = closest_valid_discipline

                    # Retrueve the discipline of the record present in the template file
                    template_record_discipline = proposal_sheet_content['Discipline'][document_index]
                    if template_record_discipline and not pd.isna(template_record_discipline) and template_record_discipline not in valid_disciplines:
                        closest_valid_discipline = utils.find_closest_match(template_record_discipline, valid_disciplines)
                        if closest_valid_discipline:
                            self.template_manager.update_cell(
                                process_name,
                                SHEET_NAME,
                                document_index,
                                'Discipline',
                                closest_valid_discipline
                            )
                            template_record_discipline = closest_valid_discipline

                    # *** Lazy Data Migration (Temporary, Suggested, Not ideal for future proofing)
                    elif template_record_discipline and pd.isna(template_record_discipline):
                        record_admin_unit = record['Admin Unit']
                        if not pd.isna(record_admin_unit) and record_admin_unit in valid_disciplines:
                            self.template_mananger.update_cell(
                                process_name,
                                SHEET_NAME,
                                document_index,
                                'Discipline',
                                record_admin_unit
                            )
                            template_record_discipline = record_admin_unit
                        elif not pd.isna(record_admin_unit) and not pd.isna(record['John Jay Centers']):
                            self.template_mananger.update_cell(
                                process_name,
                                SHEET_NAME,
                                document_index,
                                'Discipline',
                                "Law and Criminal Justice"
                            )
                            template_record_discipline = "Law and Criminal Justice"

                    if project_disciplines[record_grant_id] and project_disciplines[record_grant_id] in valid_disciplines:
                        if not pd.isna(template_record_discipline) and template_record_discipline in valid_disciplines:
                            if template_record_discipline != project_disciplines[record_grant_id]:
                                self.comment_manager.append_comment(
                                    SHEET_NAME,
                                    document_index + 1,
                                    proposal_sheet_content.columns.get_loc('Discipline'),
                                    f"The record has the discipline '{project_disciplines[record_grant_id]}' in the database which differs from its value in the template. Both of which are valid disciplines."
                                )
                        else:
                            self.template_manager.update_cell(
                                process_name,
                                SHEET_NAME,
                                document_index,
                                'Discipline',
                                project_disciplines[record_grant_id]
                            )
                    else:
                        if template_record_discipline and template_record_discipline in valid_disciplines:
                            self.db_manager.update_query(
                                process_name,
                                SHEET_NAME,
                                {"Discipline":template_record_discipline},
                                "Grant_ID = ?",
                                record_grant_id
                            )
                        else:
                            if not template_record_discipline or template_record_discipline not in valid_disciplines:
                                self.comment_manager.append_comment(
                                    SHEET_NAME,
                                    document_index + 1,
                                    proposal_sheet_content.columns.get_loc('Discipline'),
                                    f"The record does not have a valid discipline in either the database or in the template."
                                )
                else:
                    self.comment_manager.append_comment(
                        SHEET_NAME,
                        document_index + 1,
                        proposal_sheet_content.columns.get_loc('proposalLegacyNumber'),
                        f"Id {record_grant_id} is not associated with any record in the database."
                    )

            print(f"Process is {round(last_index/num_sheet_rows * 100)}% complete")
    return Process(
        logic,
        process_name,
        "Process populates the 'Discipline' column of the awards in the template document with the value the record is assigned in the Microsoft Access database. Additionally, the process also catches various types of issues found in the data from multiple sources such as the template file and the database and logs them."
    )

def populate_template_department(self):
    process_name = 'Populate Template Departments'
    def logic():
        # ------------------------- LU_Department table is polluted with invalid values (Approach is currently unusable) ------------------------------
        # # Retrieve the departments from the table LU_Department in the database
        # department_query = "SELECT LU_Department AS Name FROM LU_Department"
        # department_result = self.db_manager.execute_query(department_query)
        # valid_departments = [value['Name'] for value in department_result]
        # ---------------------------------------------------------------------------------------------------------------------------------------------

        # --------------------------------------- Request file with valid departments (Alternative approach) ------------------------------------------
        dept_file_path = utils.request_file_path("Enter the path of the file with the valid Departments", ['.xlsx'])
        # Read the contents of the file
        dept_file_content = pd.read_excel(dept_file_path)
        # valid_departments = [ dept.split(" - ")[1] for dept in file_content['Name'] ]
        valid_departments = { dept['Name'].split(" - ")[1]: dept['Primary Code'] for index, dept in dept_file_content.iterrows() }
        missing_departments = set()

        # ---------------------------------------- Request file with valid Centers (Alternative approach) ---------------------------------------------
        centers_file_path = utils.request_file_path("Enter the path of the file with the valid Centers", ['.xlsx'])
        centers_file_content = pd.read_excel(centers_file_path)
        valid_centers = {
            center['Name']: {
                'Admin Unit': center['Admin Unit'],
                'Primary Code': center['Admin Unit Code']
            } 
        for index, center in centers_file_content.iterrows() }

        # Retrieve the content of the proposal sheet
        proposal_sheet_content = self.template_manager.df[SHEET_NAME]

        last_index = 0
        batch_limit = 40
        num_sheet_rows = len(proposal_sheet_content)
        # Loop while index has not reached the number of rows in the sheet
        while last_index < num_sheet_rows:
            new_end = last_index + batch_limit
            batch_ids = proposal_sheet_content['proposalLegacyNumber'][last_index:new_end].tolist()
            last_index = new_end

            # Retrieve the Grant_ID and the Primary_Dept value of the records in the batch_ids list
            search_result = self.db_manager.select_query(
                "grants",
                ["Grant_ID","Primary_Dept"],
                f"Grant_ID IN ({','.join(['?' for _ in batch_ids])})",
                batch_ids
            )
            project_departments = { project['Grant_ID']:project['Primary_Dept'] for project in search_result }

            # Loop through every grand_id in the batch
            for index, id in enumerate(batch_ids):
                document_index = last_index - batch_limit + index
                
                # Check if the database returned a record with the id
                if id in project_departments:
                    if project_departments[id] and project_departments[id] not in valid_departments:
                        closest_valid_dept = utils.find_closest_match(project_departments[id], [dept for dept in valid_departments])
                        if closest_valid_dept:
                            self.db_manager.update_cell(
                                process_name,
                                SHEET_NAME,
                                {"Primary_Dept":closest_valid_dept},
                                "Grant_ID = ?",
                                id
                            )
                            project_departments[id] = closest_valid_dept

                    # Retrieve the department of the record present in the template file
                    template_record_unit_code = proposal_sheet_content['Admin Unit Primary Code'][document_index]
                    template_record_unit = proposal_sheet_content['Admin Unit'][document_index]
                    if template_record_unit and not pd.isna(template_record_unit) and template_record_unit not in valid_departments:
                        closest_valid_dept = utils.find_closest_match(template_record_unit, [dept for dept in valid_departments])
                        if closest_valid_dept:
                            closest_valid_dept_code = valid_departments[closest_valid_dept]
                            self.template_manager.update_cell(
                                process_name,
                                SHEET_NAME,
                                document_index,
                                'Admin Unit',
                                closest_valid_dept
                            )
                            self.template_manager.update_cell(
                                process_name,
                                SHEET_NAME,
                                document_index,
                                'Admin Unit Primary Code',
                                closest_valid_dept_code
                            )
                            template_record_unit = closest_valid_dept
                            template_record_unit_code = closest_valid_dept_code
                        else:
                            closest_valid_center = utils.find_closest_match(template_record_unit, [center for center in valid_centers])
                            if closest_valid_center:
                                center_info = valid_centers[closest_valid_center]
                                self.template_manager.update_cell(
                                    process_name,
                                    SHEET_NAME,
                                    document_index,
                                    'John Jay Centers',
                                    closest_valid_center
                                )
                                self.template_manager.update_cell(
                                    process_name,
                                    SHEET_NAME,
                                    document_index,
                                    'Admin Unit',
                                    center_info['Admin Unit']
                                )
                                self.template_manager.update_cell(
                                    process_name,
                                    SHEET_NAME,
                                    document_index,
                                    'Admin Unit Primary Code',
                                    center_info['Primary Code']
                                )
                                template_record_unit = center_info['Admin Unit']
                                template_record_unit_code = center_info['Primary Code']

                    if project_departments[id] and project_departments[id] in valid_departments:
                        if not pd.isna(template_record_unit) and template_record_unit in valid_departments:
                            if template_record_unit == project_departments[id]:
                                # Check that the correct Primary Code is assigned to the record
                                dept_code = valid_departments[project_departments[id]]
                                if template_record_unit_code != dept_code:
                                    self.template_manager.update_cell(
                                        process_name,
                                        SHEET_NAME,
                                        document_index,
                                        'Admin Unit Primary Code',
                                        dept_code
                                    )
                            else:
                                self.comment_manager.append_comment(
                                    SHEET_NAME,
                                    document_index + 1,
                                    proposal_sheet_content.columns.get_loc('Admin Unit'),
                                    f"The record has the department '{project_departments[id]}' in the database which differs from its value in the template. Both of which are valid departments."
                                )
                        else:
                            # Assign the 'Admin Unit' property of the current record the updated value
                            self.template_manager.update_cell(
                                process_name,
                                SHEET_NAME,
                                document_index,
                                'Admin Unit',
                                project_departments[id]
                            )
                            self.template_manager.update_cell(
                                process_name,
                                SHEET_NAME,
                                document_index,
                                'Admin Unit Primary Code',
                                valid_departments[project_departments[id]]
                            )
                    else:
                        if template_record_unit and template_record_unit in valid_departments:
                            self.db_manager.update_query(
                                process_name,
                                "grants",
                                {"Primary_Dept":template_record_unit},
                                "Grant_ID = ?",
                                id
                            )
                        else:
                            if not template_record_unit or template_record_unit not in valid_centers:
                                self.comment_manager.append_comment(
                                    SHEET_NAME,
                                    document_index + 1,
                                    proposal_sheet_content.columns.get_loc('Admin Unit'),
                                    f"The record does not have a valid department in either the database or in the template."
                                )
                else:
                    self.comment_manager.append_comment(
                        SHEET_NAME,
                        document_index + 1,
                        proposal_sheet_content.columns.get_loc('proposalLegacyNumber'),
                        f"Id {id} is not associated with any record in the database."
                    )

            print(f"Process is {round(last_index/num_sheet_rows * 100)}% complete")
    return Process(
        logic,
        process_name,
        "Process populates the 'Admin Unit' column of the proposals in the template document with the value the record is assigned in the Microsoft Access database. Additionally, the process also catches various types of issues found in the data from multiple sources such as the template file and the database and logs them."
    )

