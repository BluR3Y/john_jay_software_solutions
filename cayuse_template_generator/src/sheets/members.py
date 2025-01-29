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

# def determine_user_name(instance, grant):
#     project_pi = grant['Primary_PI']
#     stored_pi_info = instance.pi_data.get(project_pi)
    
#     if stored_pi_info:
#         return stored_pi_info['email'], stored_pi_info['association']
#     else:
#         raise Exception("Failed to accurately determine an investigator.")

# def determine_user_role(instance, grant):
#     project_id = grant['Grant_ID']
#     project_pi = grant['Primary_PI']
#     select_res = instance.db_manager.execute_query("SELECT * FROM PI_name WHERE PI_Grant_ID = ?;", project_id)
#     if select_res:
#         return ("Principal Investigator" if len(select_res) == 1 else "co-Principal Investigator")
#     else:
#         raise Exception("Failed to determine Investigator for grant.")

# def members_sheet_append(self, grant):
#     sheet_df = self.generated_template_manager.df[SHEET_NAME]
#     next_row = sheet_df.shape[0] + 1
    
#     project_status = grant['Status']
    
#     try:
#         grant_user_name, grant_user_association = determine_user_name(self, grant)
#     except Exception as e:
#         grant_user_association = None
#         grant_user_name = None
#         if grant['Primary_PI']:
#             l_name, f_name = grant['Primary_PI'].split(", ")
#             grant_user_name = f_name + ' ' + l_name
#         self.generated_template_manager.comment_manager.append_comment(SHEET_NAME, next_row, 4, e)
    
#     try:
#         grant_user_role = determine_user_role(self, grant)
#     except Exception as e:
#         grant_user_role = None
#         self.generated_template_manager.comment_manager.append_comment(SHEET_NAME, next_row, 5, e)

#     self.generated_template_manager.append_row(SHEET_NAME, {
#         "projectLegacyNumber": grant['Project_Legacy_Number'],
#         "form": "proposal",
#         "legacyNumber": grant['Grant_ID'],
#         "username": grant_user_name,
#         "role": grant_user_role,
#         "association 1": grant_user_association
#     })
#     if project_status == "Funded":
#         self.generated_template_manager.append_row(SHEET_NAME, {
#             "projectLegacyNumber": grant['Project_Legacy_Number'],
#             "form": "award",
#             "legacyNumber": (str(grant['Grant_ID']) + "-award"),
#             "username": grant_user_name,
#             "role": grant_user_role,
#             "association 1": grant_user_association
#         })

def determine_pi_info(instance, grant):
    investigators = instance.INVESTIGATORS
    project_investigator = grant['grant_data']['Primary_PI']
    reverse_investigators = {f"{props['name']['last']}, {props['name']['first']}": name for name, props in investigators.items()}
    num_investigators_involved = len(grant['pi_data'])
    investigator_role = ("Principal Investigator" if num_investigators_involved < 2 else ("Co-Principal Investigator" if num_investigators_involved < 3 else "Other Participant"))
    
    if project_investigator in reverse_investigators:
        investigator_info = investigators[reverse_investigators[project_investigator]]
        return investigator_info['email'], investigator_role, investigator_info['association']

    # alt_investigators = instance.INVESTIGATORS_ALT
    # if project_investigator in alt_investigators:
    #     print('marker-------------------------')
        
    existing_entry = instance.feedback_template_manager.get_entry(SHEET_NAME, "projectLegacyNumber", grant['grant_data']['Project_Legacy_Number'])
    if existing_entry != None:
        return existing_entry['username'], existing_entry['role'], existing_entry['association 1']
        
    first_name, last_name = project_investigator.split(',')
    first_name.strip()
    last_name.strip()
    return f"{first_name} {last_name}", investigator_role, None

def members_sheet_append(self, grants):
    sheet_df = self.generated_template_manager.df[SHEET_NAME]
    
    for grant_obj in reversed(grants):
        print('loopi')
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
        # if not grant_user_name:
        #     existing_entry = self.feedback_template_manager.get_entry(SHEET_NAME, "projectLegacyNumber", grant_data['Project_Legacy_Number'])
        #     if existing_entry != None:
        #         # name_first, name_last = grant_data['Primary_PI'].split(',')
        #         # name_first.strip().capitalize()
        #         # name_last.strip().capitalize()
        #         # pi_name = f"{name_last}, {name_first}"
        #         # if pi_name not in self.INVESTIGATORS_ALT:
        #         #     print('hehehe')
        #         #     self.INVESTIGATORS_ALT[pi_name] = {
        #         #         "username": existing_entry['username'],
        #         #         "association": existing_entry['association 1']
        #         #     }
                
        #         grant_user_name = existing_entry['username']
        #         grant_user_role = existing_entry['role']
        #         grant_user_association = existing_entry['association 1']
        
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
    