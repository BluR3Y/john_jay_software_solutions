from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Only imported for type checking
    from packages.migration_manager import MigrationManager
    
SHEET_NAME = "Members - Template"

def determine_pi_info(instance, grant_data, pi_data):
    investigators = instance.INVESTIGATORS
    project_investigator = grant_data['Primary_PI']
    reverse_investigators = {f"{props['name']['last']}, {props['name']['first']}": name for name, props in investigators.items()}
    num_investigators_involved = len(pi_data)
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

def members_sheet_append(self: "MigrationManager", grant_data, pi_data, existing_grant):
    gt_manager = self.generated_template_manager
    ft_manager = self.feedback_template_manager
    next_row = gt_manager.df[SHEET_NAME].shape[0] + 1
    # existing_data = ft_manager.get_entries(SHEET_NAME, {"projectLegacyNumber": grant_data['Project_Legacy_Number']}).to_dict() if existing_grant else {}
    grant_pln = grant_data['Project_Legacy_Number']
    
    existing_data = {}
    if existing_grant:
        existing_data = ft_manager.get_entries(SHEET_NAME, {"projectLegacyNumber": grant_pln}) or {}
    
    grant_user_name = None
    grant_user_association = None
    grant_user_role = None
    if grant_data['Primary_PI']:
        try:
            grant_user_name, grant_user_role, grant_user_association = determine_pi_info(self, grant_data, pi_data)
        except Exception as err:
            existing_name = existing_data.get('username')
            existing_role = existing_data.get('role')
            existing_association = existing_data.get('association 1')
            if existing_name:
                grant_user_name = existing_name
                grant_user_association = existing_association
                grant_user_role = existing_role
                gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 4, 'warning', "Investigator was determined using feedback file.")
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 4, 'error', "Grant has invalid Primary_PI in database")
            
    # if not grant_user_association:
    #     existing_entry = self.feedback_template_manager.get_entry(SHEET_NAME, "projectLegacyNumber", grant_data['Project_Legacy_Number'])
    #     if existing_entry != None:
    #         grant_user_name = existing_entry['username']
    #         grant_user_role = existing_entry['role']
    #         grant_user_association = existing_entry['association 1']
            
    #         if grant_data['Primary_PI'] not in self.INVESTIGATORS_ALT:
    #             self.INVESTIGATORS_ALT[grant_data['Primary_PI']] = {
    #                 "username": existing_entry['username'],
    #                 "association": existing_entry['association 1']
    #             }
    
    self.generated_template_manager.append_row(SHEET_NAME, {
        "projectLegacyNumber": grant_pln,
        "form": "proposal",
        "legacyNumber": grant_data['Grant_ID'],
        "username": grant_user_name,
        "role": grant_user_role,
        "association 1": grant_user_association
    })
    if grant_data['Status'] == "Funded":
        self.generated_template_manager.append_row(SHEET_NAME, {
            "projectLegacyNumber": grant_pln,
            "form": "award",
            "legacyNumber": (str(grant_data['Grant_ID']) + "-award"),
            "username": grant_user_name,
            "role": grant_user_role,
            "association 1": grant_user_association
        })