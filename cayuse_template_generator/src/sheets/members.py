from datetime import datetime

SHEET_NAME = "Members - Template"
SHEET_COLUMNS = [
    "projectLegacyNumber",
    "form",
    "legacyNumber",
    "modificationNumber",
    "username",
    "role",
    "association 1 (name)",
    "association 1",
    "credit 1",
    "association 2",
    "credit 2",
    "association 3",
    "credit 3",
    "association 4",
    "credit 4"
  ]

def determine_user_name(instance, grant):
    project_pi = grant['Primary_PI']
    stored_pi_info = instance.pi_data.get(project_pi)
    
    if stored_pi_info:
        return stored_pi_info['email'], stored_pi_info['association']
    else:
        raise Exception("Failed to accurately determine an investigator.")

def determine_user_role(instance, grant):
    project_id = grant['Grant_ID']
    project_pi = grant['Primary_PI']
    select_res = instance.db_manager.execute_query("SELECT * FROM PI_name WHERE PI_Grant_ID = ?;", project_id)
    if select_res:
        return ("Principal Investigator" if len(select_res) == 1 else "co-Principal Investigator")
    else:
        raise Exception("Failed to determine Investigator for grant.")

def members_sheet_append(self, grant):
    sheet_df = self.generated_template_manager.df[SHEET_NAME]
    next_row = sheet_df.shape[0] + 1
    
    project_status = grant['Status']
    
    try:
        grant_user_name, grant_user_association = determine_user_name(self, grant)
    except Exception as e:
        grant_user_association = None
        l_name, f_name = grant['Primary_PI'].split(", ")
        grant_user_name = f_name + ' ' + l_name
        self.generated_template_manager.comment_manager.append_comment(SHEET_NAME, next_row, 4, e)
    
    try:
        grant_user_role = determine_user_role(self, grant)
    except Exception as e:
        grant_user_role = None
        self.generated_template_manager.comment_manager.append_comment(SHEET_NAME, next_row, 5, e)

    self.generated_template_manager.append_row(SHEET_NAME, {
        "projectLegacyNumber": grant['project_legacy_number'],
        "form": "proposal",
        "legacyNumber": grant['Grant_ID'],
        "username": grant_user_name,
        "role": grant_user_role,
        "association 1": grant_user_association
    })
    if project_status == "Funded":
        self.generated_template_manager.append_row(SHEET_NAME, {
            "projectLegacyNumber": grant['project_legacy_number'],
            "form": "award",
            "legacyNumber": (str(grant['Grant_ID']) + "-award"),
            "username": grant_user_name,
            "role": grant_user_role,
            "association 1": grant_user_association
        })