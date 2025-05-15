import re

from typing import TYPE_CHECKING
from datetime import datetime
from dateutil.relativedelta import relativedelta

from modules.utils import find_closest_match

if TYPE_CHECKING:
    from .. import MigrationManager

SHEET_NAME = "Proposal - Template"

# def determine_oar_status(grant_data: dict) -> str:
#     project_status = str(grant_data.get('Status')).capitalize()

#     if project_status == "Funded":
#         project_end_date = grant_data.get('End_Date_Req') or grant_data.get('End_Date') or grant_data.get('Date_Submitted')
#         if not project_end_date:
#             raise ValueError("Grant was not assigned an End Date in the database.")
        
#         funded_threshold = datetime.strptime('2024-01-01', '%Y-%m-%d')
#         return "Active" if project_end_date >= funded_threshold else "Closed"
    
#     if project_status == "Pending":
#         project_start_date = grant_data.get('Start_Date_Req') or grant_data.get('Date_Submitted') or grant_data.get('Start_Date')
#         if not project_start_date:
#             raise ValueError("Grant was not assigned a Start Date in the database.")
        
#         pending_threshold = datetime.strptime('2024-06-30', '%Y-%m-%d')
#         return "Activate" if project_start_date >= pending_threshold else "Closed"
    
#     if project_status in ["Withdrawn", "Unsubmitted", "Rejected"]:
#         return "Closed"

# Funded, Pending, Rejected, Unsubmitted, Withdrawn
def determine_status(grant_data: dict) -> str:
    pass
    
def determine_instrument_type(instrument_types: list[str], target: str) -> tuple[str, float]:
    type = re.sub(r"^[A-Z]\s*-\s*", "", target)
    return find_closest_match(type, instrument_types)

def determine_sponsor(sponsors: dict, target: str) -> tuple[str, str, float]:
    closest_sponsor = find_closest_match(target, list(sponsors.keys()))
    if closest_sponsor:
        return (closest_sponsor[0], sponsors[closest_sponsor[0]], closest_sponsor[1])
    
def determine_activity_type(activity_types: list[str], target: str) -> str:
    if target in activity_types:
        return target
    closest_match = find_closest_match(target, activity_types, case_sensitive=False)
    if closest_match:
        return closest_match[0]


def proposals_sheet_append(
    self: "MigrationManager",
    grant_data: dict,
    total_data: list,
    rifunds_data: list):
    gen_proposal_sheet_manager = self.generated_wb_manager[SHEET_NAME]
    ref_proposal_sheet_manager = self.reference_wb_manager[SHEET_NAME] if self.reference_wb_manager else None

    next_row = gen_proposal_sheet_manager.df.shape[0]

    grant_id = grant_data.get('Grant_ID')
    grant_pln = grant_data.get('Project_Legacy_Number')

    existing_data_ref = ref_proposal_sheet_manager.find({"proposalLegacyNumber": grant_id}, return_one=True) if ref_proposal_sheet_manager else None
    existing_data = existing_data_ref.to_dict() if (existing_data_ref is not None and not existing_data_ref.empty) else {}

    # Status
    grant_ref_status = existing_data.get('status')
    grant_gen_status = None
    grant_db_status = grant_data.get('Status')
    if grant_db_status:
        try:
            determined_status = determine_status()
            if not determined_status:
                raise ValueError(f"Grant was assigned an invalid status in the database: {grant_db_status}")
            grant_gen_status = determined_status
        except Exception as err:
            gen_proposal_sheet_manager.add_issue(next_row, "status", "error", err)
    else:
        gen_proposal_sheet_manager.add_issue(next_row, "status", "error", "Grant is missing Status in database.")
    
    grant_status, status_error = self.determine_best_match(grant_ref_status, grant_gen_status)
    if status_error:
        gen_proposal_sheet_manager.add_issue(next_row, "status", "warning", status_error)
    
    # CUNY Campus
    grant_ref_campus = existing_data.get('CUNY Campus')
    grant_db_campus = grant_data.get('Prim_College')
    if not grant_db_campus:
        gen_proposal_sheet_manager.add_issue(next_row, "CUNY Campus", "error", "Grant is missing Primary College in database.")

    grant_campus, campus_error = self.determine_best_match(grant_ref_campus, grant_db_campus)
    if campus_error:
        gen_proposal_sheet_manager.add_issue(next_row, "CUNY Campus", "warning", campus_error)
    
    # Instrument Type
    grant_ref_instrument_type = existing_data.get('Instrument Type')
    grant_gen_instrument_type = None
    grant_db_instrument_type = grant_data.get('Instrument_Type')
    if grant_db_instrument_type:
        try:
            determined_instrument_type = determine_instrument_type(self.INSTRUMENT_TYPES, grant_db_instrument_type)
            if not determined_instrument_type:
                raise ValueError(f"Grant was assigned an invalid Instrument Type in the database: {grant_db_instrument_type}")
            if determined_instrument_type[1] < 90:
                gen_proposal_sheet_manager.add_issue(next_row, "Instrument Type", "warning", f"Failed to find exact match for Instrument Type '{grant_db_instrument_type}' but was similar to {determined_instrument_type[0]}")
            grant_gen_instrument_type = determined_instrument_type[0]
        except Exception as err:
            gen_proposal_sheet_manager.add_issue(next_row, "Instrument Type", "error", err)
    else:
        gen_proposal_sheet_manager.add_issue(next_row, "Instrument Type", "error", "Grant is missing Instrument Type in database.")

    grant_instrument_type, instrument_type_error = self.determine_best_match(grant_ref_instrument_type, grant_gen_instrument_type)
    if instrument_type_error:
        gen_proposal_sheet_manager.add_issue(next_row, "Instrument Type", "warning", instrument_type_error)
    
    # Sponsor
    grant_ref_sponsor_code = existing_data.get('Sponsor')
    grant_gen_sponsor_name = grant_gen_sponsor_code = None
    grant_db_sponsor = grant_data.get('Sponsor_1')
    if grant_db_sponsor:
        try:
            determined_sponsor = determine_sponsor(self.EXTERNAL_ORGS, grant_db_sponsor)
            if not determined_sponsor:
                raise ValueError(f"Grant was assigned an invalid Sponsor_1 in the database: {grant_db_sponsor}")
            if determined_sponsor[2] < 90:
                gen_proposal_sheet_manager.add_issue(next_row, "Sponsor", "warning", f"Failed to find exact match for Sponsor '{grant_db_sponsor}' but was similar to {determined_sponsor[0]}")
            grant_gen_sponsor_name, grant_gen_sponsor_code, *_ = determined_sponsor
        except Exception as err:
            grant_gen_sponsor_code = grant_db_sponsor
            gen_proposal_sheet_manager.add_issue(next_row, "Sponsor", "error", err)
    else:
        gen_proposal_sheet_manager.add_issue(next_row, "Sponsor", "error", "Grant is missing Sponsor_1 in database.")

    grant_sponsor_code, sponsor_error = self.determine_best_match(grant_ref_sponsor_code, grant_gen_sponsor_code)
    if sponsor_error:
        gen_proposal_sheet_manager.add_issue(next_row, "Sponsor", "warning", sponsor_error)

    # Instrument Type Fallback
    if not grant_gen_instrument_type:
        str_id = str(grant_data['RF_Account'])
        if str_id.startswith('6'):
            grant_gen_instrument_type = "PSC CUNY"
        elif grant_sponsor_code == 'CUNY':
            grant_gen_instrument_type = 'CUNY Internal'
        elif grant_sponsor_code.startswith('NYC') or grant_sponsor_code.startswith('NYS'):
            grant_gen_instrument_type = "NYC/NYS MOU - Interagency Agreement"
        elif grant_sponsor_code == 'NSF' or grant_sponsor_code == 'JJCOAR':
            grant_gen_instrument_type = "Grant"
        grant_instrument_type, instrument_type_error = self.determine_best_match(grant_ref_instrument_type, grant_gen_instrument_type)
        if instrument_type_error:
            gen_proposal_sheet_manager.add_issue(next_row, "Instrument Type", "warning", instrument_type_error)

    # Prime Sponsor
    grant_ref_prime_sponsor_code = existing_data.get('Prime Sponsor')
    grant_gen_prime_sponsor_name = grant_gen_prime_sponsor_code = None
    grant_db_prime_sponsor = grant_data.get('Sponsor_2')
    if grant_db_prime_sponsor:
        try:
            determined_prime_sponsor = determine_sponsor(self.EXTERNAL_ORGS, grant_db_prime_sponsor)
            if not determined_prime_sponsor:
                raise ValueError(f"Grant has invalid Sponsor_2 in database: {grant_db_prime_sponsor}")
            if determined_prime_sponsor[2] < 90:
                gen_proposal_sheet_manager.add_issue(next_row, "Prime Sponsor", "warning", f"Failed to find exact match for Prime Sponsor '{grant_db_prime_sponsor}' but was similar to {determined_prime_sponsor[0]}")
            grant_gen_prime_sponsor_name, grant_gen_prime_sponsor_code, *_ = determined_prime_sponsor
        except Exception as err:
            grant_gen_prime_sponsor_code = grant_db_prime_sponsor
            gen_proposal_sheet_manager.add_issue(next_row, "Prime Sponsor", "error", err)
    
    grant_prime_sponsor, prime_sponsor_error = self.determine_best_match(grant_ref_prime_sponsor_code, grant_gen_prime_sponsor_code)
    if prime_sponsor_error:
        gen_proposal_sheet_manager.add_issue(next_row, "Prime Sponsor", "warning", prime_sponsor_error)

    # Title
    grant_ref_title = existing_data.get('Title')
    grant_db_title = grant_data.get('Project_Title')
    if not grant_db_title:
        gen_proposal_sheet_manager.add_issue(next_row, "Title", "error", "Grant is missing Project_Title in database.")
    grant_title, title_error = self.determine_best_match(grant_ref_title, grant_db_title)
    if title_error:
        gen_proposal_sheet_manager.add_issue(next_row, "Title", "warning", title_error)

    # Start Date
    grant_ref_start_date = existing_data.get('Project Start Date')
    grant_gen_start_date = None
    grant_db_start_date = grant_data.get('Start_Date') or grant_data.get('Start_Date_Req')
    if not grant_db_start_date:
        gen_proposal_sheet_manager.add_issue(next_row, "Project Start Date", "error", "Grant does not have a start date in database.")
        if ("OAR" or " oar " in grant_title) or (grant_sponsor_code == "JJCOAR") and grant_data.get('Status_Date'):
            grant_gen_start_date = grant_data['Status_Date']
    else:
        grant_gen_start_date = grant_db_start_date

    grant_start_date, start_date_error = self.determine_best_match(grant_ref_start_date, grant_gen_start_date)
    if start_date_error:
        gen_proposal_sheet_manager.add_issue(next_row, "Project Start Date", "warning", start_date_error)
    
    # End Date
    grant_ref_end_date = existing_data.get('Project End Date')
    grant_gen_end_date = None
    grant_db_end_date = grant_data.get('End_Date') or grant_data.get('End_Date_Req')
    if not grant_db_end_date:
        gen_proposal_sheet_manager.add_issue(next_row, "Project End Date", "error", "Grant does not have an end date in database.")
        if (("OAR" or " oar " in grant_title) or (grant_sponsor_code == "JJCOAR") and grant_data.get('Status_Date')):
            grant_gen_end_date = grant_data['Status_Date']
    else:
        grant_gen_end_date = grant_db_end_date + relativedelta(years=1)

    grant_end_date, end_date_error = self.determine_best_match(grant_ref_end_date, grant_gen_end_date)
    if end_date_error:
        gen_proposal_sheet_manager.add_issue(next_row, "Project End Date", "warning", end_date_error)

    # Missing: Proposal Type

    # Activity Type
    grant_ref_activity_type = existing_data.get('Activity Type')
    grant_gen_activity_type = None
    grant_db_activity_type = grant_data.get('Award_Type')
    if grant_db_activity_type:
        try:
            determined_activity_type = find_closest_match(grant_db_activity_type, self.ACTIVITY_TYPES)
            if not determined_activity_type:
                raise ValueError(f"Grant has invalid Award_Type in database: {grant_db_activity_type}")
            if determined_activity_type[1] < 90:
                gen_proposal_sheet_manager.add_issue(next_row, "Activity Type", "warning", f"Failed to find exact match for Award_Type '{grant_db_activity_type}' but is similar to '{determined_activity_type[0]}'")
            grant_gen_activity_type = determined_activity_type[0]
        except Exception as err:
            gen_proposal_sheet_manager.add_issue(next_row, "Activity Type", "error", err)
    else:
        gen_proposal_sheet_manager.add_issue(next_row, "Activity Type", "error", "Grant is missing Award_Type in database.")

    grant_activity_type, activity_type_error = self.determine_best_match(grant_ref_activity_type, grant_gen_activity_type)
    if activity_type_error:
        gen_proposal_sheet_manager.add_issue(next_row, "Activity Type", "warning", activity_type_error)
    
    # Discipline
    grant_ref_discipline = existing_data.get('Discipline')
    grant_gen_discipline = None
    grant_db_discipline = grant_data.get('Discipline')
    if grant_db_discipline:
        determined_discipline = find_closest_match(grant_db_discipline, self.DISCIPLINES)
        if not determined_discipline:
            raise ValueError(f"Grant has invalid Discipline in database: {grant_db_discipline}")
        if determined_discipline[1] < 90:
            gen_proposal_sheet_manager.add_issue(next_row, "Discipline", "warning", f"Exact match for grant discipline '{grant_db_discipline}' was not found but is similar to '{determined_discipline[0]}'")
        grant_gen_discipline = determined_discipline[0]
    else:
        gen_proposal_sheet_manager.add_issue(next_row, "Discipline", "error", "Grant is missing Discipline in database.")

    grant_discipline, discipline_error = self.determine_best_match(grant_ref_discipline, grant_gen_discipline)
    if discipline_error:
        gen_proposal_sheet_manager.add_issue(next_row, "Discipline", "warning", discipline_error)
    

    gen_proposal_sheet_manager.append_row({
        "projectLegacyNumber": grant_pln,
        "proposalLegacyNumber": grant_id,
        "status": grant_status,
        "Proposal Legacy Number": grant_pln,
        "CUNY Campus": grant_campus,
        "Instrument Type": grant_instrument_type,
        "Sponsor": grant_sponsor_code,
        "Prime Sponsor": grant_prime_sponsor,
        "Title": grant_title,
        "Project Start Date": grant_start_date.date(),
        "Project End Date": grant_end_date.date(),
        "Proposal Type": "",
        "Activity Type": grant_activity_type,
        "Discipline": grant_discipline,
        "Abstract": "",
        "Number of Budget Periods": "",
        "Indirect Rate Cost Type": "",
        "IDC Rate": "",
        "IDC Cost Type Explanation": "",
        "Total Direct Costs": "",
        "Total Indirect Costs": "",
        "Total Sponsor Costs": "",
        "IDC Rate Less OnCampus Rate": "",
        "Reassigned Time YN": "",
        "Reassigned Time Details": "",
        "Subrecipient": "",
        "Subrecipient Names": "",
        "Human Subjects": "",
        "IRB Protocol Status": "",
        "IRB Approval Date": "",
        "Animal Subjects": "",
        "Hazardous Materials": "",
        "Export Control": "",
        "Additional Comments": "",
        "Submission Date": "",
        "John Jay Centers": "",
        "Admin Unit": "",
    })