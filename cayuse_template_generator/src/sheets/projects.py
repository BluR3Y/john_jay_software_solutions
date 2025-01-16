from datetime import datetime

SHEET_NAME = "Project - Template"
SHEET_COLUMNS = ["projectLegacyNumber", "title", "status"]


# When Start_Date_Req and End_Date_Req use Date_Submitted
# def determine_status(grant):
#     status_threshold = datetime.strptime('2024-01-01', '%Y-%m-%d')
#     project_status = grant['Status']
#     project_start_date = grant['Start_Date_Req']
#     project_end_date = grant['End_Date_Req']

#     if project_status != "Rejected":
#         if project_start_date and project_end_date:
#             if project_status == "Funded":
#                 return ("Active" if project_end_date >= status_threshold else "Closed")
#             elif project_status == "Pending":
#                 return ("Active" if project_start_date >= status_threshold else "Closed")
#             else:
#                 raise Exception("Grant was assigned a status that is not valid.")
#         else:
#             raise Exception("Grant is missing start/end date which is required to determine the status.")
#     else:
#         return "Closed"

# Needs fixing
def determine_status(grant):
    status_threshold = datetime.strptime('2024-01-01', '%Y-%m-%d')
    project_status = grant['Status']
    project_start_date = grant['Start_Date_Req']
    project_end_date = grant['End_Date_Req']

    if project_status != "Rejected":
        if project_start_date and project_end_date:
            if project_status == "Funded":
                return ("Active" if project_end_date >= status_threshold else "Closed")
            elif project_status == "Pending":
                pending_threshold = datetime.strptime('2024-06-30', '%Y-%m-%d')
                project_date_submitted = grant['Date_Submitted']
                return ("Active" if  project_date_submitted >= pending_threshold else "Closed")
            else:
                raise Exception("Grant was assigned a status that is not valid.")
        else:
            raise Exception("Grant is missing start/end date which is required to determine the status.")
    else:
        return "Closed"

def projects_sheet_append(self, grant):
    sheet_df = self.generated_template_manager.df[SHEET_NAME]
    next_row = sheet_df.shape[0] + 1
    
    try:
        grant_status = determine_status(grant)
    except Exception as e:
        grant_status = None
        self.generated_template_manager.comment_manager.append_comment(SHEET_NAME, next_row, 2, e)
    
    self.generated_template_manager.append_row(SHEET_NAME, {
        "projectLegacyNumber": grant['Project_Legacy_Number'],
        "title": grant['Project_Title'],
        "status": grant_status
    })