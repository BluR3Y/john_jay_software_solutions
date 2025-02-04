from typing import TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    # Only imported for type checking
    from packages.migration_manager import MigrationManager

SHEET_NAME = "Project - Template"
SHEET_COLUMNS = ["projectLegacyNumber", "title", "status"]

def determine_grant_status(grant_data: dict):
    project_status = str(grant_data['Status']).capitalize()
    
    if project_status == "Funded":
        project_end_date = grant_data['End_Date_Req'] or grant_data['End_Date'] or grant_data['Date_Submitted']
        if not project_end_date:
            raise ValueError("Grant was not assigned an End Date in the database. Which is required to determine its status.")
            
        funded_threshold = datetime.strptime('2024-01-01', '%Y-%m-%d')
        return "Active" if project_end_date >= funded_threshold else "Closed"
    elif project_status == "Pending":
        project_start_date = grant_data['Start_Date_Req'] or grant_data['Date_Submitted'] or grant_data['Start_Date']
        if not project_start_date:
            raise ValueError("Grant was not assigned a Start Date in the database. Which is required to determine its status.")
        
        pending_threshold =  datetime.strptime('2024-06-30', '%Y-%m-%d')
        return "Active" if project_start_date >= pending_threshold else "Closed"
    elif project_status in ["Withdrawn", "Unsubmitted", "Rejected"]:
        return "Closed"
    

def projects_sheet_append(self: "MigrationManager", grant_data: dict, existing_grant: bool = False):
    gt_manager = self.generated_template_manager
    ft_manager = self.feedback_template_manager
    next_row = gt_manager.df[SHEET_NAME].shape[0] + 1
    
    grant_pln = grant_data['Project_Legacy_Number']
    if not grant_pln:
        gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 0, "error", "Grant is missing Project Legacy Number")

    existing_data = {}
    if existing_grant:
        existing_data = ft_manager.get_entries(SHEET_NAME, {"projectLegacyNumber": grant_pln}) or {}
    
    grant_title = grant_data['Project_Title']
    if not grant_title:
        gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 1, "error", "Grant is missing Project Title in database.")        
        existing_title = existing_data.get('title')
        if existing_title:
            grant_title = existing_title
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 1, "notice", "Title was determined using feedback file.")

    grant_status = grant_data['Status']
    grant_oar = None
    if grant_status:
        try:
            determined_oar = determine_grant_status(grant_data)
            if not determined_oar:
                raise ValueError(f"Grant was assigned an invalid status in the database: {grant_status}")
            grant_oar = determined_oar
        except Exception as err:
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 2, 'error', err)
    if not grant_oar:
        existing_oar = existing_data.get('status')
        if existing_oar:
            grant_oar = existing_oar
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 2, 'notice', "Status was determined using feedback file.")

    gt_manager.append_row(
        SHEET_NAME, {
            "projectLegacyNumber": grant_pln,
            "title": grant_title,
            "status": grant_oar
        }
    )