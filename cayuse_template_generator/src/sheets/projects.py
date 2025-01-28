from methods.shared_populating import determine_grant_status

SHEET_NAME = "Project - Template"
SHEET_COLUMNS = ["projectLegacyNumber", "title", "status"]


def projects_sheet_append(self, grants):    
    for index, grant_obj in enumerate(grants, start=1):
        grant_data = grant_obj['grant_data']
        
        grant_legacy_num = grant_data['Project_Legacy_Number']
        if not grant_legacy_num:
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                0,
                "Grant was not assigned a title in the database."
            )
            
        grant_title = grant_data['Project_Title']
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
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                2,
                e
            )
            
        self.generated_template_manager.append_row(
            SHEET_NAME, {
                "projectLegacyNumber": grant_legacy_num,
                "title": grant_title,
                "status": grant_status
            }
        )