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
    gen_proposals_sheet_manager = self.generated_wb_manager["Proposal - Template"]

    proposal_data_ref = gen_proposals_sheet_manager.find({"projectLegacyNumber": grant_pln}, return_one=True)
    proposal_data = proposal_data_ref.to_dict() if not proposal_data_ref.empty else {}

    investigator_association = proposal_data.get('Admin Unit')

    # association type = If email is determined: Internal; Not determined: None
    # association = admin unit code

    grant_pi_name = grant_data.get('Primary_PI')
    grant_pi_id = determine_pi_id(self, grant_pi_name, pi_data)
    grant_pi_data = self.INVESTIGATORS[grant_pi_id] if grant_pi_id else {}


    gen_members_sheet_manager.append_row({
        "projectLegacyNumber": grant_pln,
        "form": "proposal",
        "legacyNumber": grant_id,
        "modificationNumber": 0,
        "associationType": "Internal" if grant_pi_id else None,
        "username": grant_pi_data.get('email'),
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
            "associationType": "Internal" if grant_pi_id else None,
            "username": grant_pi_data.get('email'),
            "personId": grant_pi_id,
            "personName": grant_pi_name,
            "role": "PI",
            "association 1": investigator_association
        })