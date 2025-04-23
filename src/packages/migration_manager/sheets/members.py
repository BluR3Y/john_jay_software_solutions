from typing import TYPE_CHECKING
from modules.utils import find_closest_match, extract_titles

if TYPE_CHECKING:
    # Only imported for type checking
    from packages.migration_manager import MigrationManager
    
SHEET_NAME = "Members - Template"

def determine_pi_info(instance, grant_data, pi_data):
    grant_pi = grant_data['Primary_PI']
    
    closest_pi = find_closest_match(grant_pi, [pi['PI_name'] for pi in pi_data], case_sensitive=False)
    if (closest_pi):
        pi_obj = next((item for item in pi_data if item['PI_name'] == closest_pi), None)
        return (pi_obj['PI_name'], pi_obj['PI_role'] or 'PI')

def determine_pi_association(instance, pi_name):
    investigators = instance.INVESTIGATORS

    closest_pi = find_closest_match(pi_name, [pi['name']['full'] for pi in investigators.values()], case_sensitive=False)
    if (closest_pi):
        pi_obj = next((pi for pi in investigators.values() if pi['name']['full'] == closest_pi), None)
        return pi_obj['email'] ,pi_obj['association']

def members_sheet_append(
        self: "MigrationManager",
        grant_data,
        pi_data
    ):
    gt_manager = self.generated_template_manager
    ft_manager = self.feedback_template_manager
    next_row = gt_manager.df[SHEET_NAME].shape[0] + 1
    grant_pln = grant_data['Project_Legacy_Number']

    # existing_data = ft_manager.find(SHEET_NAME, {"projectLegacyNumber": grant_pln}, return_one=True, to_dict='records') or {}
    existing_data_ref = ft_manager.find(SHEET_NAME, {"projectLegacyNumber": grant_pln}, return_one=True)
    existing_data = existing_data_ref.to_dict() if existing_data_ref is not None else {}
    
    investigator_name = None
    investigator_role = None
    if len(pi_data) == 1:
        investigator_name = pi_data[0]['PI_name']
        investigator_role = pi_data[0]['PI_role'] or 'PI'
    elif len(pi_data):
        try:
            determined_pi_info = determine_pi_info(self, grant_data, pi_data)
            if not determine_pi_info:
                raise ValueError(f"Could not determine pi info")
            investigator_name, investigator_role = determined_pi_info
        except Exception as err:
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 4, 'error', err)
    
    if not investigator_name:
        investigator_name = grant_data['Primary_PI']

    investigator_association = None
    investigator_email = None
    if (investigator_name):
        try:
            retrieved_association = determine_pi_association(self, investigator_name)
            if not retrieved_association:
                raise ValueError(f"Could not determine pi association for: {investigator_name}")
            investigator_email, investigator_association = retrieved_association
        except Exception as err:
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 7, 'error', err)
    if (not investigator_association):
        existing_association = existing_data.get('association 1')
        if existing_association:
            investigator_association = existing_association
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 7, 'notice', "Association was retrieved from template file")
    if (not investigator_email):
        existing_email = existing_data.get('username')
        if existing_email:
            investigator_email = existing_email
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 4, 'notice', "Username was retrieved from template file")
        else:
            l_name, f_name = investigator_name.split(',')
            l_name.strip()
            f_name.strip()
            investigator_email = f"{f_name} {l_name}"

    # Last Here: Fixing Members
    self.generated_template_manager.append_row(
        self.process_name,
        SHEET_NAME, {
        "projectLegacyNumber": grant_pln,
        "form": "proposal",
        "legacyNumber": grant_data['Grant_ID'],
        "username": investigator_email,
        "role": investigator_role,
        "association 1": investigator_association
    })
    if grant_data['Status'] == "Funded":
        self.generated_template_manager.append_row(
            self.process_name,
            SHEET_NAME, {
            "projectLegacyNumber": grant_pln,
            "form": "award",
            "legacyNumber": (str(grant_data['Grant_ID']) + "-award"),
            "username": investigator_email,
            "role": investigator_role,
            "association 1": investigator_association
        })