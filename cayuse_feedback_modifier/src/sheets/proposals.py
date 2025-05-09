import pandas as pd
from methods import utils
from datetime import datetime
from classes.Process import Process

SHEET_NAME = "Proposal - Template"

def populate_template_discipline(self):
    process_name = 'Populate Template Disciplines'
    def logic():
        # Retrieve the content of the proposal sheet
        proposal_sheet_content = self.template_manager.df[SHEET_NAME]

        # Retrieve the disciplines from the table LU_Discipline in the database
        discipline_result = self.db_manager.select_query(
            "LU_Discipline",
            ["Name"])
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
                ["Grant_ID", "Discipline"],
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
                                "grants",
                                {"Discipline":closest_valid_discipline},
                                f"Grant_ID = ?",
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
                            self.template_manager.update_cell(
                                process_name,
                                SHEET_NAME,
                                document_index,
                                'Discipline',
                                record_admin_unit
                            )
                            template_record_discipline = record_admin_unit
                        elif not pd.isna(record_admin_unit) and not pd.isna(record['John Jay Centers']):
                            self.template_manager.update_cell(
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
                                "grants",
                                {"Discipline":template_record_discipline},
                                f"Grant_ID = ?",
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
                            self.db_manager.update_query(
                                process_name,
                                "grants",
                                {"Primary_Dept":closest_valid_dept},
                                f"Grant_ID = ?",
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
                                "Admin Unit",
                                closest_valid_dept
                            )
                            self.template_manager.update_cell(
                                process_name,
                                SHEET_NAME,
                                document_index,
                                "Admin Unit Primary Code",
                                closest_valid_dept_code
                            )
                            template_record_unit = closest_valid_dept
                            template_record_unit_code = closest_valid_dept_code
                        else:
                            closest_valid_center = utils.find_closest_match(template_record_unit, [center for center in valid_centers])
                            if closest_valid_center:
                                center_info = valid_centers[closest_valid_center]
                                prev_record_center = proposal_sheet_content['John Jay Centers'][document_index]
                                self.template_manager.update_cell(
                                    process_name,
                                    SHEET_NAME,
                                    document_index,
                                    "John Jay Centers",
                                    closest_valid_center
                                )
                                self.template_manager.update_cell(
                                    process_name,
                                    SHEET_NAME,
                                    document_index,
                                    "Admin Unit",
                                    center_info['Admin Unit']
                                )
                                self.template_manager.update_cell(
                                    process_name,
                                    SHEET_NAME,
                                    document_index,
                                    "Admin Unit Primary Code",
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
                                        "Admin Unit Primary Code",
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
                                "Admin Unit",
                                project_departments[id]
                            )
                            self.template_manager.update_cell(
                                process_name,
                                SHEET_NAME,
                                document_index,
                                "Admin Unit Primary Code",
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

def populate_project_status(self):
    process_name = "Populate Template Status"
    def logic():
        # Retrieve the content of the sheet
        proposal_sheet_content = self.template_manager.df[SHEET_NAME]
        status_threshold = datetime.strptime('2024-01-01', '%Y-%m-%d')
        # ** Missing Logging
        last_index = 0
        batch_limit = 40
        num_sheet_rows = len(proposal_sheet_content)
        # Loop while the index has not reached the number of rows in the sheet
        while last_index < num_sheet_rows:
            new_end = last_index + batch_limit
            # Retrieve all the records in the dataframe in the batch range
            batch_records = proposal_sheet_content.iloc[last_index:new_end]
            last_index = new_end

            batch_ids = batch_records['proposalLegacyNumber']
            search_result = self.db_manager.select_query(
                "grants",
                ["Grant_ID","Start_Date_Req","End_Date_Req", "Status"],
                f"Grant_ID IN ({','.join(['?' for _ in batch_ids])})",
                *batch_ids
            )
            search_db_data = { data['Grant_ID']: data for data in search_result }

            for document_index, record_template_data in batch_records.iterrows():
                record_grant_id = record_template_data['proposalLegacyNumber']
                record_db_data = search_db_data.get(record_grant_id)
                if record_db_data:
                    record_template_status = record_template_data['status']
                    record_template_oar = record_template_data['OAR Status']
                    record_db_oar = record_db_data['Status']
                    if not pd.isna(record_template_oar) and record_db_oar:
                        are_equivalent = ("Pending" if record_template_oar == "Submitted to Sponsor" else record_template_oar) == record_db_oar
                        if not are_equivalent:
                            absolute_states = ['Funded','Rejected']
                            is_template_oar_absolute = record_template_oar in absolute_states
                            is_db_oar_absolute = record_db_oar in absolute_states
                            if is_template_oar_absolute ^ is_db_oar_absolute:
                                if is_template_oar_absolute:
                                    new_db_oar = "Pending" if record_template_oar == "Submitted to Sponsor" else record_template_oar
                                    self.db_manager.update_query(
                                        process_name,
                                        "grants",
                                        {"Status":new_db_oar},
                                        "Grant_ID = ?",
                                        record_grant_id
                                    )
                                    record_db_oar = new_db_oar
                                else:
                                    # new_template_oar = "Submitted to Sponsor" if record_db_oar == "Pending" else record_db_oar
                                    new_template_oar = record_db_oar
                                    self.template_manager.update_cell(
                                        process_name,
                                        SHEET_NAME,
                                        document_index,
                                        "OAR Status",
                                        new_template_oar
                                    )
                                    record_template_oar = new_template_oar
                            else:
                                self.comment_manager.append_comment(
                                    SHEET_NAME,
                                    document_index + 1,
                                    proposal_sheet_content.columns.get_loc('OAR Status'),
                                    f"The record has a different OAR Status in the database ({record_db_oar}). This form of inconsistency can cause incorrect data to be generated."
                                )
                    elif not pd.isna(record_template_oar) or record_db_oar:
                        if pd.isna(record_template_oar):
                            # new_template_oar = "Submitted to Sponsor" if record_db_oar == "Pending" else record_db_oar
                            new_template_oar = record_db_oar
                            self.template_manager.update_cell(
                                process_name,
                                SHEET_NAME,
                                document_index,
                                "OAR Status",
                                new_template_oar
                            )
                            record_template_oar = new_template_oar
                        else:
                            new_db_oar = "Pending" if record_template_oar == "Submitted to Sponsor" else record_template_oar
                            self.db_manager.update_query(
                                process_name,
                                "grants",
                                {"Status":new_db_oar},
                                "Grant_ID = ?",
                                record_grant_id
                            )
                            record_db_oar = new_db_oar
                    else:
                        self.comment_manager.append_comment(
                            SHEET_NAME,
                            document_index + 1,
                            proposal_sheet_content.columns.get_loc('OAR Status'),
                            f"The record does not have a Status value in either the template or the database."
                        )

                    if record_template_oar != "Rejected":
                        record_template_start_date = record_template_data['Project Start Date']
                        record_db_start_date = record_db_data['Start_Date_Req']
                        if pd.isna(record_template_start_date):
                            if record_db_start_date:
                                self.template_manager.update_cell(
                                    process_name,
                                    SHEET_NAME,
                                    document_index,
                                    "Project Start Date",
                                    record_db_start_date
                                )
                                record_template_start_date = record_db_start_date
                            else:
                                self.comment_manager.append_comment(
                                    SHEET_NAME,
                                    document_index + 1,
                                    proposal_sheet_content.columns.get_loc('Project Start Date'),
                                    f"The record does not have a Project Start Date value in either the template or the database."
                                )
                        else:
                            if not record_db_start_date:
                                self.db_manager.update_query(
                                    process_name,
                                    "grants",
                                    {"Start_Date_Req":record_template_start_date},
                                    "Grant_ID = ?",
                                    record_grant_id
                                )
                                record_db_start_date = record_template_start_date
                            elif record_template_start_date != record_db_start_date:
                                self.comment_manager.append_comment(
                                    SHEET_NAME,
                                    document_index + 1,
                                    proposal_sheet_content.columns.get_loc('Project Start Date'),
                                    f"The record has a different Start date in the database ({record_db_start_date}). This form of inconsistency can cause incorrect data to be generated."
                                )

                        record_template_end_date = record_template_data['Project End Date']
                        record_db_end_date = record_db_data['End_Date_Req']
                        if pd.isna(record_template_end_date):
                            if record_db_end_date:
                                self.template_manager.update_cell(
                                    process_name,
                                    SHEET_NAME,
                                    document_index,
                                    "Project End Date",
                                    record_db_end_date.strftime("%Y-%m-%d")
                                )
                                record_template_end_date = record_db_end_date
                            else:
                                self.comment_manager.append_comment(
                                    SHEET_NAME,
                                    document_index + 1,
                                    proposal_sheet_content.columns.get_loc('Project End Date'),
                                    f"The record does not have a Project End Date value in either the template or the database."
                                )
                        else:
                            if not record_db_end_date:
                                self.db_manager.update_query(
                                    process_name,
                                    "grants",
                                    {"End_Date_Req":record_template_end_date},
                                    "Grant_ID = ?",
                                    record_grant_id
                                )
                                record_db_end_date = record_template_end_date
                            elif record_template_end_date != record_db_end_date:
                                self.comment_manager.append_comment(
                                    SHEET_NAME,
                                    document_index + 1,
                                    proposal_sheet_content.columns.get_loc('Project End Date'),
                                    f"The record has a different End date in the database ({record_db_end_date}). This form of inconsistency can cause incorrect data to be generated."
                                )
                        
                        determined_status = None
                        if record_template_oar == "Funded":
                            determined_status = "Active" if record_template_end_date >= status_threshold else "Closed"
                        elif record_template_oar == "Pending":
                            determined_status = "Active" if record_template_start_date >= status_threshold else "Closed"
                        elif record_template_oar == "Rejected":
                            determined_status = "Closed"

                        if not determined_status:
                            self.comment_manager.append_comment(
                                SHEET_NAME,
                                document_index + 1,
                                proposal_sheet_content.columns.get_loc('status'),
                                f"A correct status was not able to be determined for this record. Please check other cells in the record for possible issues."
                            )
                        elif record_template_status != determined_status:
                            self.template_manager.update_cell(
                                process_name,
                                SHEET_NAME,
                                document_index,
                                "status",
                                determined_status
                            )
                    elif record_template_status != "Rejected":
                        self.template_manager.update_cell(
                            process_name,
                            SHEET_NAME,
                            document_index,
                            "status",
                            "Closed"
                        )
                else:
                    self.comment_manager.append_comment(
                        SHEET_NAME,
                        document_index + 1,
                        proposal_sheet_content.columns.get_loc('proposalLegacyNumber'),
                        f"The record with grant_id {record_grant_id} does not exist in the database."
                    )
    return Process(
        logic,
        process_name,
        "This process goes through every record in the Proposals sheet and determines the appropriate status for the records."
    )

# Needs improving
def validate_project_instrument_type(self):
    process_name = "Validate Template Instrument Type"
    def logic():
        # Retrieve the content of the sheet
        proposal_sheet_content = self.template_manager.df[SHEET_NAME]
        valid_instrument_types = ['Grant', 'Contract', 'Cooperative Agreement', 'Incoming Subaward', 'NYC/NYS MOU - Interagency Agreement', 'PSC CUNY', 'CUNY Internal']

        for index, type in enumerate(proposal_sheet_content['Instrument Type']):
            if not pd.isna(type):
                if type not in valid_instrument_types:
                    self.comment_manager.append_comment(
                        SHEET_NAME,
                        index + 1,
                        proposal_sheet_content.columns.get_loc('Instrument Type'),
                        "Record has an invalid instrument type."
                    )
            else:
                self.comment_manager.append_comment(
                    SHEET_NAME,
                    index + 1,
                    proposal_sheet_content.columns.get_loc('Instrument Type'),
                    "Instrument Type can not be left empty."
                )

    return Process(
        logic,
        process_name,
        "This process valides the value under 'Instrument Type' for each record in the proposal sheet."
    )