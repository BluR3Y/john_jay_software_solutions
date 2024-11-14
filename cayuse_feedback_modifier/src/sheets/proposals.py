import pandas as pd
from methods import utils
from datetime import datetime
from classes.Process import Process

SHEET_NAME = "Proposal - Template"

def populate_template_discipline(self):
    process_name = 'Populate Template Disciplines'
    def logic():
        sheet_logger = dict()
        # Retrieve the content of the proposal sheet
        proposal_sheet_content = self.template_manager.df[SHEET_NAME]

        # Retrieve the disciplines from the table LU_Discipline in the database
        discipline_query = "SELECT Name FROM LU_Discipline;"
        discipline_result = self.db_manager.execute_query(discipline_query)
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
            search_query = f"SELECT Grant_ID, Discipline FROM grants WHERE Grant_ID IN ({','.join(['?' for _ in batch_ids])})"
            search_result = self.db_manager.execute_query(search_query, *batch_ids)
            project_disciplines = { project['Grant_ID']:project['Discipline'] for project in search_result }

            for document_index, record in batch_records.iterrows():
                record_grant_id = record['proposalLegacyNumber']

                # Check if the database returned a record with the id
                if record_grant_id in project_disciplines:
                    if project_disciplines[record_grant_id] and project_disciplines[record_grant_id] not in valid_disciplines:
                        closest_valid_discipline = utils.find_closest_match(project_disciplines[record_grant_id], valid_disciplines)
                        if closest_valid_discipline:
                            update_query = f"""
                                UPDATE grants
                                SET Discipline = ?
                                WHERE Grant_ID = ?
                            """
                            self.db_manager.execute_query(update_query, closest_valid_discipline, record_grant_id)
                            sheet_logger[f"database:{record_grant_id}"] = {
                                "Discipline": f"{project_disciplines[record_grant_id]}:{closest_valid_discipline}"
                            }
                            project_disciplines[record_grant_id] = closest_valid_discipline

                    # Retrueve the discipline of the record present in the template file
                    template_record_discipline = proposal_sheet_content['Discipline'][document_index]
                    if template_record_discipline and not pd.isna(template_record_discipline) and template_record_discipline not in valid_disciplines:
                        closest_valid_discipline = utils.find_closest_match(template_record_discipline, valid_disciplines)
                        if closest_valid_discipline:
                            proposal_sheet_content.loc[document_index, 'Discipline'] = closest_valid_discipline
                            sheet_logger[f"template:{record_grant_id}"] = {
                                "Discipline": f"{template_record_discipline}:{closest_valid_discipline}"
                            }
                            template_record_discipline = closest_valid_discipline

                    # *** Lazy Data Migration (Temporary, Suggested, Not ideal for future proofing)
                    elif template_record_discipline and pd.isna(template_record_discipline):
                        record_admin_unit = record['Admin Unit']
                        if not pd.isna(record_admin_unit) and record_admin_unit in valid_disciplines:
                            proposal_sheet_content.loc[document_index, 'Discipline'] = record_admin_unit
                            sheet_logger[f"template:{record_grant_id}"] = {
                                "Discipline": f"{template_record_discipline}:{record_admin_unit}"
                            }
                            template_record_discipline = record_admin_unit
                        elif not pd.isna(record_admin_unit) and not pd.isna(record['John Jay Centers']):
                            proposal_sheet_content.loc[document_index, 'Discipline'] = "Law and Criminal Justice"
                            sheet_logger[f"template:{record_grant_id}"] = {
                                "Discipline": f"{template_record_discipline}:{"Law and Criminal Justice"}"
                            }
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
                            proposal_sheet_content.loc[document_index, 'Discipline'] = project_disciplines[record_grant_id]
                            sheet_logger[f"template:{record_grant_id}"] = {
                                "Discipline": f"{template_record_discipline}:{project_disciplines[record_grant_id]}"
                            }
                    else:
                        if template_record_discipline and template_record_discipline in valid_disciplines:
                            update_query = f"""
                                UPDATE grants
                                SET Discipline = ?
                                WHERE Grant_ID = ?
                            """
                            self.db_manager.execute_query(update_query, template_record_discipline, record_grant_id)
                            sheet_logger[f"database:{record_grant_id}"] = {
                                "Discipline": f"{project_disciplines[record_grant_id]}:{template_record_discipline}"
                            }
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

        if sheet_logger:
            self.log_manager.append_logs(SHEET_NAME, process_name, sheet_logger)
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

        sheet_logger = dict()
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
            search_query = f"""
                SELECT Grant_ID, Primary_Dept
                FROM grants
                WHERE Grant_ID IN ({','.join(['?' for _ in batch_ids])})
            """
            search_result = self.db_manager.execute_query(search_query, batch_ids)
            project_departments = { project['Grant_ID']:project['Primary_Dept'] for project in search_result }

            # Loop through every grand_id in the batch
            for index, id in enumerate(batch_ids):
                document_index = last_index - batch_limit + index
                
                # Check if the database returned a record with the id
                if id in project_departments:
                    if project_departments[id] and project_departments[id] not in valid_departments:
                        closest_valid_dept = utils.find_closest_match(project_departments[id], [dept for dept in valid_departments])
                        if closest_valid_dept:
                            update_query = f"""
                                UPDATE grants
                                SET Primary_Dept = ?
                                WHERE Grant_ID = ?
                            """
                            self.db_manager.execute_query(update_query, closest_valid_dept, id)
                            sheet_logger[f"database:{id}"] = {
                                "Admin Unit": f"{project_departments[id]}:{closest_valid_dept}"
                            }
                            project_departments[id] = closest_valid_dept

                    # Retrieve the department of the record present in the template file
                    template_record_unit_code = proposal_sheet_content['Admin Unit Primary Code'][document_index]
                    template_record_unit = proposal_sheet_content['Admin Unit'][document_index]
                    if template_record_unit and not pd.isna(template_record_unit) and template_record_unit not in valid_departments:
                        closest_valid_dept = utils.find_closest_match(template_record_unit, [dept for dept in valid_departments])
                        if closest_valid_dept:
                            closest_valid_dept_code = valid_departments[closest_valid_dept]
                            proposal_sheet_content.loc[document_index, 'Admin Unit'] = closest_valid_dept
                            proposal_sheet_content.loc[document_index, 'Admin Unit Primary Code'] = closest_valid_dept_code
                            sheet_logger[f"template:{id}"] = {
                                "Admin Unit": f"{template_record_unit}:{closest_valid_dept}",
                                "Admin Unit Primary Code": f"{template_record_unit_code}:{closest_valid_dept_code}"
                            }
                            template_record_unit = closest_valid_dept
                            template_record_unit_code = closest_valid_dept_code
                        else:
                            closest_valid_center = utils.find_closest_match(template_record_unit, [center for center in valid_centers])
                            if closest_valid_center:
                                center_info = valid_centers[closest_valid_center]
                                prev_record_center = proposal_sheet_content['John Jay Centers'][document_index]
                                proposal_sheet_content.loc[document_index, 'John Jay Centers'] = closest_valid_center
                                proposal_sheet_content.loc[document_index, 'Admin Unit'] = center_info['Admin Unit']
                                proposal_sheet_content.loc[document_index, 'Admin Unit Primary Code'] = center_info['Primary Code']
                                sheet_logger[f"template:{id}"] = {
                                    "John Jay Centers": f"{prev_record_center}:{closest_valid_center}",
                                    "Admin Unit": f"{template_record_unit}:{center_info['Admin Unit']}",
                                    "Admin Unit Primary Code": f"{template_record_unit_code}:{center_info['Primary Code']}"
                                }
                                template_record_unit = center_info['Admin Unit']
                                template_record_unit_code = center_info['Primary Code']

                    if project_departments[id] and project_departments[id] in valid_departments:
                        if not pd.isna(template_record_unit) and template_record_unit in valid_departments:
                            if template_record_unit == project_departments[id]:
                                # Check that the correct Primary Code is assigned to the record
                                dept_code = valid_departments[project_departments[id]]
                                if template_record_unit_code != dept_code:
                                    proposal_sheet_content.loc[document_index, 'Admin Unit Primary Code'] = dept_code
                                    sheet_logger[f"template:{id}"] = {
                                        "Admin Unit Primary Code": f"{template_record_unit_code}:{dept_code}"
                                    }
                            else:
                                self.comment_manager.append_comment(
                                    SHEET_NAME,
                                    document_index + 1,
                                    proposal_sheet_content.columns.get_loc('Admin Unit'),
                                    f"The record has the department '{project_departments[id]}' in the database which differs from its value in the template. Both of which are valid departments."
                                )
                        else:
                            # Assign the 'Admin Unit' property of the current record the updated value
                            proposal_sheet_content.loc[document_index, 'Admin Unit'] = project_departments[id]
                            proposal_sheet_content.loc[document_index, 'Admin Unit Primary Code'] = valid_departments[project_departments[id]]
                            sheet_logger[f"template:{id}"] = {
                                'Admin Unit': f"{template_record_unit}:{project_departments[id]}",
                                'Admin Unit Primary Code': f"{template_record_unit_code}:{valid_departments[project_departments[id]]}"
                            }
                    else:
                        if template_record_unit and template_record_unit in valid_departments:
                            update_query = """
                                UPDATE grants
                                SET Primary_Dept = ?
                                WHERE Grant_ID = ?
                            """
                            self.db_manager.execute_query(update_query, template_record_unit, id)
                            sheet_logger[f"database:{id}"] = {
                                "Primary_Dept": f"{project_departments[id]}:{template_record_unit}"
                            }
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
        
        if sheet_logger:
            self.log_manager.append_logs(SHEET_NAME, process_name, sheet_logger)
    return Process(
        logic,
        process_name,
        "Process populates the 'Admin Unit' column of the proposals in the template document with the value the record is assigned in the Microsoft Access database. Additionally, the process also catches various types of issues found in the data from multiple sources such as the template file and the database and logs them."
    )

def populate_project_status(self):
    process_name = "Populate Template Status"
    def logic():
        sheet_logger = dict()
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
            search_query = f"SELECT Grant_ID, Start_Date_Req AS Start_Date, End_Date_Req AS End_Date, Status as OAR_Status FROM grants WHERE Grant_ID IN ({','.join(['?' for _ in batch_ids])})"
            search_result = self.db_manager.execute_query(search_query, *batch_ids)
            search_db_data = { data['Grant_ID']: data for data in search_result }

            for document_index, record_template_data in batch_records.iterrows():
                record_grant_id = record_template_data['proposalLegacyNumber']
                record_db_data = search_db_data.get(record_grant_id)
                if record_db_data:
                    record_template_status = record_template_data['status']
                    record_template_oar = record_template_data['OAR Status']
                    record_db_oar = record_db_data['OAR_Status']
                    if not pd.isna(record_template_oar) and record_db_oar:
                        are_equivalent = ("Pending" if record_template_oar == "Submitted to Sponsor" else record_template_oar) == record_db_oar
                        if not are_equivalent:
                            absolute_states = ['Funded','Rejected']
                            is_template_oar_absolute = record_template_oar in absolute_states
                            is_db_oar_absolute = record_db_oar in absolute_states
                            if is_template_oar_absolute ^ is_db_oar_absolute:
                                if is_template_oar_absolute:
                                    update_query = """
                                        UPDATE grants
                                        SET OAR_Status = ?
                                        WHERE Grant_ID = ?
                                    """
                                    new_db_oar = "Pending" if record_template_oar == "Submitted to Sponsor" else record_template_oar
                                    self.db_manager.execute_query(update_query, new_db_oar, record_grant_id)
                                    sheet_logger[f"database:{record_grant_id}"] = {
                                        "OAR_Status": f"{record_db_oar}:{new_db_oar}"
                                    }
                                    record_db_oar = new_db_oar
                                else:
                                    new_template_oar = "Submitted to Sponsor" if record_db_oar == "Pending" else record_db_oar
                                    proposal_sheet_content.loc[document_index, 'OAR Status'] = new_template_oar
                                    sheet_logger[f"template:{record_grant_id}"] = {
                                        "OAR Status": f"{record_template_oar}:{new_template_oar}"
                                    }
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
                            new_template_oar = "Submitted to Sponsor" if record_db_oar == "Pending" else record_db_oar
                            proposal_sheet_content.loc[document_index, 'OAR Status'] = new_template_oar
                            sheet_logger[f"template:{record_grant_id}"] = {
                                "OAR Status": f"{record_template_oar}:{new_template_oar}"
                            }
                            record_template_oar = new_template_oar
                        else:
                            new_db_oar = "Pending" if record_template_oar == "Submitted to Sponsor" else record_template_oar
                            update_query = """
                                UPDATE grants
                                SET OAR_Status = ?
                                WHERE Grant_ID = ?
                            """
                            self.db_manager.execute_query(update_query, new_db_oar, record_grant_id)
                            sheet_logger[f"database:{record_grant_id}"] = {
                                "OAR_Status": f"{record_db_oar}:{new_db_oar}"
                            }
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
                        record_db_start_date = record_db_data['Start_Date']
                        if pd.isna(record_template_start_date):
                            if record_db_start_date:
                                proposal_sheet_content.loc[document_index, 'Project Start Date'] = record_db_start_date
                                sheet_logger[f"template:{record_grant_id}"] = {
                                    "Project Start Date": f"{record_template_start_date}:{record_db_start_date}"
                                }
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
                                update_query = """
                                    UPDATE grants
                                    SET Start_Date_Req = ?
                                    WHERE Grant_ID = ?
                                """
                                self.db_manager.execute_query(update_query, record_template_start_date, record_grant_id)
                                sheet_logger[f"database:{record_grant_id}"] = {
                                    "Start_Date_Req": f"{record_db_start_date}:{record_template_start_date}"
                                }
                                record_db_start_date = record_template_start_date
                            elif record_template_start_date != record_db_start_date:
                                self.comment_manager.append_comment(
                                    SHEET_NAME,
                                    document_index + 1,
                                    proposal_sheet_content.columns.get_loc('Project Start Date'),
                                    f"The record has a different Start date in the database ({record_db_start_date}). This form of inconsistency can cause incorrect data to be generated."
                                )

                        record_template_end_date = record_template_data['Project End Date']
                        record_db_end_date = record_db_data['End_Date']
                        if pd.isna(record_template_end_date):
                            if record_db_end_date:
                                proposal_sheet_content.loc[document_index, 'Project End Date'] = record_db_end_date
                                sheet_logger[f"template:{record_grant_id}"] = {
                                    "Project End Date": f"{record_template_end_date}:{record_db_end_date}"
                                }
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
                                update_query = """
                                    UPDATE grants
                                    SET End_Date_Req = ?
                                    WHERE Grant_ID = ?
                                """
                                self.db_manager.execute_query(update_query, record_template_end_date, record_grant_id)
                                sheet_logger[f"database:{record_grant_id}"] = {
                                    "End_Date_Req": f"{record_db_end_date}:{record_template_end_date}"
                                }
                                record_db_end_date = record_template_end_date
                            elif record_template_end_date != record_db_end_date:
                                self.comment_manager.append_comment(
                                    SHEET_NAME,
                                    document_index + 1,
                                    proposal_sheet_content.columns.get_loc('Project End Date'),
                                    f"The record has a different End date in the database ({record_db_end_date}). This form of inconsistency can cause incorrect data to be generated."
                                )
                        
                        determined_status = ("Active" if record_template_end_date >= status_threshold else "Closed") if record_template_end_date else None
                        if not determined_status:
                            self.comment_manager.append_comment(
                                SHEET_NAME,
                                document_index + 1,
                                proposal_sheet_content.columns.get_loc('status'),
                                f"A correct status was not able to be determined for this record. Please check other cells in the record for possible issues."
                            )
                        elif record_template_status != determined_status:
                            proposal_sheet_content.loc[document_index, 'status'] = determined_status
                            sheet_logger[f"template:{record_grant_id}"] = { "status": f"{record_template_status}:{determined_status}" }
                    elif record_template_status != "Rejected":
                        proposal_sheet_content.loc[document_index, 'status'] = "Closed"
                        sheet_logger[f"template:{record_grant_id}"] = { "status": f"{record_template_data['status']}:Closed" }
                else:
                    self.comment_manager.append_comment(
                        SHEET_NAME,
                        document_index + 1,
                        proposal_sheet_content.columns.get_loc('proposalLegacyNumber'),
                        f"The record with grant_id {record_grant_id} does not exist in the database."
                    )

        if sheet_logger:
            self.log_manager.append_logs(SHEET_NAME, process_name, sheet_logger)

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