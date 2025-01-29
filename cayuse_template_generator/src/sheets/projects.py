from methods.shared_populating import determine_grant_status

SHEET_NAME = "Project - Template"
SHEET_COLUMNS = ["projectLegacyNumber", "title", "status"]


def projects_sheet_append(self, grants):    
    for index, grant_obj in enumerate(grants, start=1):
        grant_data = grant_obj['grant_data']
        grant_pln = grant_data['Project_Legacy_Number']
        existing_grant = {}
        
        if grant_pln:
            template_row = self.feedback_template_manager.get_entry(SHEET_NAME, "projectLegacyNumber", grant_pln)
            if template_row != None:
                existing_grant = template_row
        else:
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                0,
                "Grant was not assigned a title in the database."
            )
            
        grant_title = grant_data['Project_Title'] or existing_grant.get('title')
        if not grant_title:
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                1,
                "Grant was not assigned a Project Title in the database."
            )
            
        grant_status = None
        try:
            grant_status = determine_grant_status(grant_data)
        except Exception as e:
            grant_status = existing_grant.get('status')
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                2,
                e
            )
            
        self.generated_template_manager.append_row(
            SHEET_NAME, {
                "projectLegacyNumber": grant_pln,
                "title": grant_title,
                "status": grant_status
            }
        )