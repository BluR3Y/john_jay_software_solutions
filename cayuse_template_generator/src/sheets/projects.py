from datetime import datetime

SHEET_NAME = "Project - Template"
SHEET_COLUMNS = ["projectLegacyNumber", "title", "status"]

def determine_status(grant):
    project_status = grant['Status']
    if project_status:
        if project_status == "Funded":
            funded_threshold = datetime.strptime('2024-01-01', '%Y-%m-%d')
            project_end_date = grant['End_Date_Req'] or grant['Date_Submitted']
            if project_end_date:
                return ("Active" if project_end_date >= funded_threshold else "Closed")
            else:
                raise Exception("Funded grant is not assigned an 'End_Date_Req' value in the database which is crucial towards determining a status.")
        elif project_status == "Pending":
            pending_threshold =  datetime.strptime('2024-06-30', '%Y-%m-%d')
            project_start_date = grant['Start_Date_Req'] or grant['Date_Submitted']
            if project_start_date:
                return ("Active" if project_start_date >= pending_threshold else "Closed")
            else:
                raise Exception("Pending grant is missing a 'Start_Date_Req' value in the database which is crucial towards determining a status.")
        elif project_status in ["Withdrawn","Unsubmitted","Rejected"]:
            return "Closed"
        else:
            raise Exception("Grant was assigned an invalid Status in the database.")
    else:
        raise Exception("Grant is missing a Status in the database.")

def projects_sheet_append(self, grant):
    sheet_df = self.generated_template_manager.df[SHEET_NAME]
    next_row = sheet_df.shape[0] + 1
    
    grant_legacy_num = grant['Project_Legacy_Number']
    if not grant_legacy_num:
        self.generated_template_manager.comment_manager.append_comment(SHEET_NAME, next_row, 0, "Grant was not assigned a title in the database.")

    grant_title = grant['Project_Title']
    if not grant_title:
        self.generated_template_manager.comment_manager.append_comment(SHEET_NAME, next_row, 1, "Grant was not assigned a Project Title in the database.")

    grant_status = None
    try:
        grant_status = determine_status(grant)
    except Exception as e:
        self.generated_template_manager.comment_manager.append_comment(SHEET_NAME, next_row, 2, e)
    
    self.generated_template_manager.append_row(SHEET_NAME, {
        "projectLegacyNumber": grant['Project_Legacy_Number'],
        "title": grant['Project_Title'],
        "status": grant_status
    })