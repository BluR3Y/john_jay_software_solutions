from typing import TYPE_CHECKING
from ....modules.utils import find_closest_match
import pandas as pd

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
    grant_data: dict
):
    grant_pln = grant_data.get('Project_Legacy_Number')
    grant_id = grant_data.get('Grant_ID')

    gen_members_sheet_manager = self.generated_wb_manager[SHEET_NAME]
    next_row = gen_members_sheet_manager.df.shape[0]

    ref_members_sheet_manager = self.reference_wb_manager[SHEET_NAME] if self.reference_wb_manager else None
    gen_proposals_sheet_manager = self.generated_wb_manager["Proposal - Template"]

    proposal_data_ref = gen_proposals_sheet_manager.find({"projectLegacyNumber": grant_pln}, return_one=True)
    proposal_data = proposal_data_ref.to_dict() if not proposal_data_ref.empty else {}

    existing_data_ref = ref_members_sheet_manager.find({"projectLegacyNumber": grant_pln}, return_one=True) if ref_members_sheet_manager else pd.DataFrame()
    existing_data = existing_data_ref.to_dict() if not existing_data_ref.empty else {}

    investigator_association = proposal_data.get('Admin Unit')

    grant_ref_pi_email = existing_data.get('username')
    grant_gen_pi_email = grant_pi_name = None

    if grant_ref_pi_email:
        try:
            determined_email = find_closest_match(grant_ref_pi_email, list(self.INVESTIGATORS.keys()), case_sensitive=False)
            if not determined_email:
                raise ValueError(f"Referenced workbook has invalid username: {grant_ref_pi_email}")
            elif determined_email[1] < 90:
                gen_members_sheet_manager.add_issue(next_row, "username", "warning", f"Failed to determine exact PI but was similar to: {determined_email[0]}")
            
            grant_gen_pi_email = determined_email[0]
        except Exception as err:
            gen_members_sheet_manager.add_issue(next_row, "username", "error", err)

    if not grant_gen_pi_email:
        grant_db_pi_name = grant_data.get('Primary_PI')
        grant_ref_pi_name = existing_data.get('personName')
        grant_gen_pi_name = grant_pi_name = None
        # try:
        #     determined_pi_name = find_closest_match(grant_db_pi_name, [pi.get('PI_name') for pi in pi_data], case_sensitive=False)
        #     if not determined_pi_name:
        #         raise ValueError(f"Investigator information could not be determined for the name: {grant_db_pi_name}")
        #     if determined_pi_name[1] < 90:
        #         gen_members_sheet_manager.add_issue(next_row, "personName", "warning", f"Failed to determine exact PI but was similar to: {determined_pi_name[0]}")
        #     grant_gen_pi_name = determined_pi_name[0]
        # except Exception as err:
        #     gen_members_sheet_manager.add_issue(next_row, "personName", "error", err)

        # name_best_match = self.determine_best_match(grant_ref_pi_name, grant_gen_pi_name)
        # if name_best_match:
        #     grant_pi_name, name_error = name_best_match
        #     if name_error:
        #         gen_members_sheet_manager.add_issue(next_row, "personName", "warning", name_error)
        grant_pi_name = grant_db_pi_name
        
        try:
            determined_pi_email = find_closest_match(grant_pi_name, list(self.FORMAT_INVESTIGATORS.keys()), case_sensitive=False)
            if not determined_pi_email:
                raise ValueError(f'Investigator information could not be determined using using the email: {grant_pi_name}')
            if determined_pi_email[1] < 90:
                gen_members_sheet_manager.add_issue(next_row, "username", "warning", f"Failed to determine exact PI email but was similar to: {determined_pi_email[0]}")
            grant_gen_pi_email = self.FORMAT_INVESTIGATORS.get(determined_pi_email[0])
        except Exception as err:
            gen_members_sheet_manager.add_issue(next_row, "username", "error", err)

    grant_pi_data = None
    if grant_gen_pi_email:
        grant_pi_data = self.INVESTIGATORS.get(grant_gen_pi_email)
        f_name, m_name, l_name = grant_pi_data.get('name').values()
        grant_pi_name = f"{l_name}, {f"{f_name} {m_name}" if m_name else f_name}"
    else:
        grant_pi_data = {
            "email": existing_data.get('username'),
            "empl_id": existing_data.get('personId')
        }
        grant_pi_name = existing_data.get('personName')

    gen_members_sheet_manager.append_row({
        "projectLegacyNumber": grant_pln,
        "form": "proposal",
        "legacyNumber": grant_id,
        "modificationNumber": 0,
        "associationType": "Internal" if grant_pi_data.get('empl_id') else "External",
        "username": grant_pi_data.get('email'),
        "personId": grant_pi_data.get('empl_id'),
        "personName": grant_pi_name,
        "role": "PI",
        "association": investigator_association,
        "association 1": existing_data.get('association 1')
    })
    if grant_data.get('Status') == "Funded":
        gen_members_sheet_manager.append_row({
            "projectLegacyNumber": grant_pln,
            "form": "award",
            "legacyNumber": f"{grant_id}-award",
            "modificationNumber": 0,
            "associationType": "Internal" if grant_pi_data.get('empl_id') else "External",
            "username": grant_pi_data.get('email'),
            "personId": grant_pi_data.get('empl_id'),
            "personName": grant_pi_name,
            "role": "PI",
            "association": investigator_association,
            "association 1": existing_data.get('association 1')
        })