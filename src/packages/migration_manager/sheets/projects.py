from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .. import MigrationManager

SHEET_NAME = "Project - Template"

def projects_sheet_append(self: "MigrationManager", grant_data: dict):
    gen_projects_sheet_manager = self.generated_wb_manager[SHEET_NAME]
    gen_proposals_sheet_manager = self.generated_wb_manager["Proposal - Template"]
    grant_pln = grant_data.get('Project_Legacy_Number')

    proposals_data_ref = gen_proposals_sheet_manager.find({"projectLegacyNumber": grant_pln}, return_one=True)
    proposals_data = proposals_data_ref.to_dict() if proposals_data_ref is not None else {}
    
    grant_title = proposals_data.get('Title')
    grant_status = proposals_data.get('status')
    if grant_status in ["Funded", "In Development"]:
        grant_status = "Active"

    gen_projects_sheet_manager.append_row({
        "projectLegacyNumber": grant_pln,
        "title": grant_title,
        "status": grant_status
    })