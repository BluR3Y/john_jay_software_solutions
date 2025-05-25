from typing import TYPE_CHECKING
from modules.utils import find_closest_match

if TYPE_CHECKING:
    from .. import MigrationManager

SHEET_NAME = "Members - Template"


def determine_pi_id(self, grant_pi, pi_data) -> int:
    closest_pi_name = find_closest_match(grant_pi, [pi.get('PI_name') for pi in pi_data], case_sensitive=False)
    if not closest_pi_name:
        return
    
    closest_person = find_closest_match(closest_pi_name[0], list(self.FORMAT_INVESTIGATORS.keys()), case_sensitive=False)
    return self.FORMAT_INVESTIGATORS[closest_person[0]] if closest_person else None

def members_sheet_append(
    self: "MigrationManager",
    grant_data: dict,
    pi_data: dict
):
    grant_pln = grant_data.get('Project_Legacy_Number')
    grant_id = grant_data.get('Grant_ID')

    gen_members_sheet_manager = self.generated_wb_manager[SHEET_NAME]
    next_row = gen_members_sheet_manager.df.shape[0]

    ref_members_sheet_manager = self.reference_wb_manager[SHEET_NAME] if self.reference_wb_manager else None
    gen_proposals_sheet_manager = self.generated_wb_manager["Proposal - Template"]

    proposal_data_ref = gen_proposals_sheet_manager.find({"projectLegacyNumber": grant_pln}, return_one=True)
    proposal_data = proposal_data_ref.to_dict() if not proposal_data_ref.empty else {}

    existing_data_ref = ref_members_sheet_manager.find({"projectLegacyNumber": grant_pln}, return_one=True)
    existing_data = existing_data_ref.to_dict() if not existing_data_ref.empty else {}

    investigator_association = proposal_data.get('Admin Unit')

    grant_db_pi_name = grant_data.get('Primary_PI')
    grant_ref_pi_name = existing_data.get('personName')
    grant_gen_pi_name = grant_pi_name = None
    try:
        determined_pi_name = find_closest_match(grant_db_pi_name, [pi.get('PI_name') for pi in pi_data], case_sensitive=False)
        if not determined_pi_name:
            raise ValueError("")
        grant_gen_pi_name = determined_pi_name[0]
    except Exception as err:
        pass

    grant_pi_name_best_match = self.determine_best_match(grant_ref_pi_name, grant_gen_pi_name)
    if grant_pi_name_best_match:
        grant_pi_name, pi_name_error = grant_pi_name_best_match
        if pi_name_error:
            gen_members_sheet_manager.add_issue(next_row, "username", "warning", grant_pi_error)

    # association type = If email is determined: Internal; Not determined: None
    # association = admin unit code

    # grant_pi_name = grant_data.get('Primary_PI')
    # grant_pi_id = determine_pi_id(self, grant_pi_name, pi_data)
    # grant_pi_data = self.INVESTIGATORS[grant_pi_id] if grant_pi_id else {}

    grant_ref_pi_email = existing_data.get('username')
    grant_gen_pi_email = grant_pi = None
    try:
        determined_pi = find_closest_match(grant_pi_name, list(self.FORMAT_INVESTIGATORS.keys()), case_sensitive=False)
        if not determined_pi:
            raise ValueError("")
        grant_gen_pi_email = self.FORMAT_INVESTIGATORS[determined_pi[0]]
    except Exception as err:
        pass

    grant_pi_best_match = self.determine_best_match(grant_ref_pi_email, grant_gen_pi_email)
    if grant_pi_best_match:
        grant_pi, grant_pi_error = grant_pi_best_match
        if grant_pi_error:
            gen_members_sheet_manager.add_issue(next_row, "username", "warning", grant_pi_error)
    
    grant_pi_data = self.INVESTIGATORS.get(grant_pi)
    grant_association_type = "Internal" if grant_pi_data else None
    grant_pi_id = grant_pi_data.get('empl_id') if grant_pi_data else None

    gen_members_sheet_manager.append_row({
        "projectLegacyNumber": grant_pln,
        "form": "proposal",
        "legacyNumber": grant_id,
        "modificationNumber": 0,
        "associationType": grant_association_type,
        "username": grant_pi,
        "personId": grant_pi_id,
        "personName": grant_pi_name,
        "role": "PI",
        "association 1": investigator_association
    })
    if grant_data.get('Status') == "Funded":
        gen_members_sheet_manager.append_row({
            "projectLegacyNumber": grant_pln,
            "form": "award",
            "legacyNumber": f"{grant_id}-award",
            "modificationNumber": 0,
            "associationType": grant_association_type,
            "username": grant_pi,
            "personId": grant_pi_id,
            "personName": grant_pi_name,
            "role": "PI",
            "association 1": investigator_association
        })