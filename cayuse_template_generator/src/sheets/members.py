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

def determine_pi_info(instance, grant):
    investigators = instance.INVESTIGATORS
    project_investigator = grant['grant_data']['Primary_PI']
    reverse_investigators = {f"{props['name']['last']}, {props['name']['first']}": name for name, props in investigators.items()}
    num_investigators_involved = len(grant['pi_data'])
    investigator_role = ("Principal Investigator" if num_investigators_involved < 2 else ("Co-Principal Investigator" if num_investigators_involved < 3 else "Other Participant"))
    
    if project_investigator in reverse_investigators:
        investigator_info = investigators[reverse_investigators[project_investigator]]
        return investigator_info['email'], investigator_role, investigator_info['association']
        
    alt_investigators = instance.INVESTIGATORS_ALT
    if project_investigator in alt_investigators:
        investigator_info = alt_investigators[project_investigator]
        return investigator_info['username'], investigator_role, investigator_info['association']
        
    first_name, last_name = project_investigator.split(',')
    first_name.strip()
    last_name.strip()
    return f"{first_name} {last_name}", investigator_role, None

def members_sheet_append(self, grants):
    sheet_df = self.generated_template_manager.df[SHEET_NAME]
    
    for grant_obj in reversed(grants):
        next_row = sheet_df.shape[0] + 1
        grant_data = grant_obj['grant_data']
        
        grant_user_name = None
        grant_user_association = None
        grant_user_role = None
        try:
            grant_user_name, grant_user_role, grant_user_association = determine_pi_info(self, grant_obj)
        except Exception as e:
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                next_row,
                4,
                e
            )

        if not grant_user_association:
            existing_entry = self.feedback_template_manager.get_entry(SHEET_NAME, "projectLegacyNumber", grant_data['Project_Legacy_Number'])
            if existing_entry != None:
                grant_user_name = existing_entry['username']
                grant_user_role = existing_entry['role']
                grant_user_association = existing_entry['association 1']
                
                if grant_data['Primary_PI'] not in self.INVESTIGATORS_ALT:
                    self.INVESTIGATORS_ALT[grant_data['Primary_PI']] = {
                        "username": existing_entry['username'],
                        "association": existing_entry['association 1']
                    }
                
        self.generated_template_manager.append_row(SHEET_NAME, {
            "projectLegacyNumber": grant_data['Project_Legacy_Number'],
            "form": "proposal",
            "legacyNumber": grant_data['Grant_ID'],
            "username": grant_user_name,
            "role": grant_user_role,
            "association 1": grant_user_association
        })
        if grant_data['Status'] == "Funded":
            self.generated_template_manager.append_row(SHEET_NAME, {
                "projectLegacyNumber": grant_data['Project_Legacy_Number'],
                "form": "award",
                "legacyNumber": (str(grant_data['Grant_ID']) + "-award"),
                "username": grant_user_name,
                "role": grant_user_role,
                "association 1": grant_user_association
            })
    