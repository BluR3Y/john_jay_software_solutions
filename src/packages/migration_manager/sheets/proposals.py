import re

from typing import TYPE_CHECKING
from datetime import datetime
from dateutil.relativedelta import relativedelta

from modules.utils import find_closest_match

if TYPE_CHECKING:
    from .. import MigrationManager

SHEET_NAME = "Proposal - Template"

# Version#1:
# DB Types: Funded, Pending, Rejected, Unsubmitted, Withdrawn
# WB Types: Approved, Closed, Funded, In Development, Submitted to Sponsor, Under Consideration, Under Review
# def determine_status(grant_data: dict) -> str:
#     project_status = grant_data.get('Status').capitalize()

#     if project_status in ["Withdrawn", "Unsubmitted", "Rejected"]:
#         return "Closed"
    
#     if project_status == "Funded":
#         project_end_date = grant_data.get('End_Date_Req') or grant_data.get('End_Date') or grant_data.get('Date_Submitted')
#         if not project_end_date:
#             raise ValueError("Grant was not assigned an End Date in the database.")
        
#         funded_threshold = datetime.strptime('2024-01-01', '%Y-%m-%d')
#         return "Funded" if project_end_date >= funded_threshold else "Closed"

#     if project_status == "Pending":
#         project_start_date = grant_data.get('Start_Date_Req') or grant_data.get('Date_Submitted') or grant_data.get('Start_Date')
#         if not project_start_date:
#             raise ValueError("Grant was not assigned a Start Date in the database.")
        
#         pending_threshold = datetime.strptime('2024-06-30', '%Y-%m-%d')
#         return "Submitted to Sponsor" if project_start_date >= pending_threshold else "Closed"
    
# Version#2 (simplified):
    # Funded -> Funded
    # Pending -> Submitted to Sponsor
    # Rejected -> Closed
def determine_status(grant_data: dict) -> str:
    project_status = grant_data.get('Status').capitalize()

    if project_status in ["Withdrawn", "Unsubmitted", "Rejected"]:
        return "Closed"
    
    if project_status == "Pending":
        return "Submitted to Sponsor"
    
    if project_status == "Funded":
        return project_status
    
def determine_instrument_type(instrument_types: list[str], target: str) -> tuple[str, float]:
    type = re.sub(r"^[A-Z]\s*-\s*", "", target)
    return find_closest_match(type, instrument_types, case_sensitive=False)

def determine_sponsor(sponsors: dict, target: str) -> tuple[str, str, float]:
    closest_sponsor = find_closest_match(target, list(sponsors.keys()), case_sensitive=False)
    if closest_sponsor:
        return (closest_sponsor[0], sponsors[closest_sponsor[0]].get('Primary Code'), closest_sponsor[1])
    
def determine_activity_type(activity_types: list[str], target: str) -> str:
    if target in activity_types:
        return target
    closest_match = find_closest_match(target, activity_types, case_sensitive=False)
    if closest_match:
        return closest_match[0]
    
def map_yearly_cost(cost_data: list[dict], period_key: str, amount_key: str) -> dict:
    period_data = {}
    for item in cost_data:
        period = item.get(period_key)
        period_data[int(period)] = item.get(amount_key)
    
    if len(period_data) > 1:
        for idx in [period_data.keys()][1:]:
            if not period_data.get(idx - 1):
                return None

    return period_data

def determine_yearly_cost(cost_data: dict, format_str: str) -> dict:
    yearly_cost = {}
    for num_year in sorted(cost_data.keys()):
        formatted_year = format_str.format(num_year)
        yearly_cost[formatted_year] = cost_data[num_year]
    
    return yearly_cost

def determine_yearly_direct_cost(total_cost: dict, indirect_cost: dict, format_str: str) -> dict:
    direct_costs = {}

    shared_periods = list(set(total_cost.keys()) & set(indirect_cost.keys()))
    for num_year in sorted(shared_periods):
        formatted_year = format_str.format(num_year)
        direct_costs[formatted_year] = round(total_cost[num_year] - indirect_cost[num_year], 2)

    return direct_costs

def proposals_sheet_append(
    self: "MigrationManager",
    grant_data: dict,
    total_data: list,
    rifunds_data: list,
    costshare_data: list
):
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
    grant_status = None
    if grant_db_status:
        try:
            determined_status = determine_status(grant_data)
            if not determined_status:
                raise ValueError(f"Grant was assigned an invalid status in the database: {grant_db_status}")
            grant_gen_status = determined_status
        except Exception as err:
            gen_proposal_sheet_manager.add_issue(next_row, "status", "error", err)
    else:
        gen_proposal_sheet_manager.add_issue(next_row, "status", "error", "Grant is missing Status in database.")
    
    status_best_match = self.determine_best_match(grant_ref_status, grant_gen_status)
    if status_best_match:
        grant_status, status_error = status_best_match
        if status_error:
            gen_proposal_sheet_manager.add_issue(next_row, "status", "warning", status_error)
    
    # CUNY Campus
    grant_ref_campus = existing_data.get('CUNY Campus')
    grant_db_campus = grant_data.get('Prim_College')
    grant_campus = None
    if not grant_db_campus:
        gen_proposal_sheet_manager.add_issue(next_row, "CUNY Campus", "error", "Grant is missing Primary College in database.")

    campus_best_match = self.determine_best_match(grant_ref_campus, grant_db_campus)
    if campus_best_match:
        grant_campus, campus_error = campus_best_match
        if campus_error:
            gen_proposal_sheet_manager.add_issue(next_row, "CUNY Campus", "warning", campus_error)
    
    # Instrument Type
    grant_ref_instrument_type = existing_data.get('Instrument Type')
    grant_gen_instrument_type = None
    grant_db_instrument_type = grant_data.get('Instrument_Type')
    grant_instrument_type = None
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

    instrument_type_best_match = self.determine_best_match(grant_ref_instrument_type, grant_gen_instrument_type)
    if instrument_type_best_match:
        grant_instrument_type, instrument_type_error = instrument_type_best_match
        if instrument_type_error:
            gen_proposal_sheet_manager.add_issue(next_row, "Instrument Type", "warning", instrument_type_error)
    
    # Sponsor
    grant_ref_sponsor_code = existing_data.get('Sponsor')
    grant_gen_sponsor_name = grant_gen_sponsor_code = None
    grant_db_sponsor = grant_data.get('Sponsor_1')
    grant_sponsor_code = None
    if grant_db_sponsor:
        try:
            determined_sponsor = determine_sponsor(self.EXTERNAL_ORGS, grant_db_sponsor)
            if not determined_sponsor:
                raise ValueError(f"Grant was assigned an invalid Sponsor_1 in the database: {grant_db_sponsor}")
            if determined_sponsor[2] < 90:
                gen_proposal_sheet_manager.add_issue(next_row, "Sponsor", "warning", f"Failed to find exact match for Sponsor '{grant_db_sponsor}' but was similar to {determined_sponsor[0]}")
            grant_gen_sponsor_name, grant_gen_sponsor_code, *_ = determined_sponsor
        except Exception as err:
            grant_gen_sponsor_name = grant_db_sponsor
            gen_proposal_sheet_manager.add_issue(next_row, "Sponsor", "error", err)
    else:
        gen_proposal_sheet_manager.add_issue(next_row, "Sponsor", "error", "Grant is missing Sponsor_1 in database.")

    sponsor_best_match = self.determine_best_match(grant_ref_sponsor_code, grant_gen_sponsor_code)
    if sponsor_best_match:
        grant_sponsor_code, sponsor_error = sponsor_best_match
        if sponsor_error:
            gen_proposal_sheet_manager.add_issue(next_row, "Sponsor", "warning", sponsor_error)

    # Fallback: Instrument Type
    if not grant_gen_instrument_type:
        str_id = str(grant_data['RF_Account'])
        if str_id.startswith('6'):
            grant_gen_instrument_type = "PSC CUNY"
        elif grant_sponsor_code:
            if grant_sponsor_code == 'CUNY':
                grant_gen_instrument_type = 'CUNY Internal'
            elif grant_sponsor_code.startswith('NYC') or grant_sponsor_code.startswith('NYS'):
                grant_gen_instrument_type = "NYC/NYS MOU - Interagency Agreement"
            elif grant_sponsor_code == 'NSF' or grant_sponsor_code == 'JJCOAR':
                grant_gen_instrument_type = "Grant"

        instrument_type_best_match = self.determine_best_match(grant_ref_instrument_type, grant_gen_instrument_type)
        if instrument_type_best_match:
            grant_instrument_type, instrument_type_error = instrument_type_best_match
            if instrument_type_error:
                gen_proposal_sheet_manager.add_issue(next_row, "Instrument Type", "warning", instrument_type_error)

    # Prime Sponsor
    grant_ref_prime_sponsor_code = existing_data.get('Prime Sponsor')
    grant_gen_prime_sponsor_name = grant_gen_prime_sponsor_code = None
    grant_db_prime_sponsor = grant_data.get('Sponsor_2')
    grant_prime_sponsor = None
    if grant_db_prime_sponsor:
        try:
            determined_prime_sponsor = determine_sponsor(self.EXTERNAL_ORGS, grant_db_prime_sponsor)
            if not determined_prime_sponsor:
                raise ValueError(f"Grant has invalid Sponsor_2 in database: {grant_db_prime_sponsor}")
            if determined_prime_sponsor[2] < 90:
                gen_proposal_sheet_manager.add_issue(next_row, "Prime Sponsor", "warning", f"Failed to find exact match for Prime Sponsor '{grant_db_prime_sponsor}' but was similar to {determined_prime_sponsor[0]}")
            grant_gen_prime_sponsor_name, grant_gen_prime_sponsor_code, *_ = determined_prime_sponsor
        except Exception as err:
            grant_gen_prime_sponsor_name = grant_db_prime_sponsor
            gen_proposal_sheet_manager.add_issue(next_row, "Prime Sponsor", "error", err)
    
    prime_sponsor_best_match = self.determine_best_match(grant_ref_prime_sponsor_code, grant_gen_prime_sponsor_code)
    if prime_sponsor_best_match:
        grant_prime_sponsor, prime_sponsor_error = prime_sponsor_best_match
        if prime_sponsor_error:
            gen_proposal_sheet_manager.add_issue(next_row, "Prime Sponsor", "warning", prime_sponsor_error)

    # Title
    grant_ref_title = existing_data.get('Title')
    grant_db_title = grant_data.get('Project_Title')
    grant_title = None
    if not grant_db_title:
        gen_proposal_sheet_manager.add_issue(next_row, "Title", "error", "Grant is missing Project_Title in database.")
    title_best_match = self.determine_best_match(grant_ref_title, grant_db_title)
    if title_best_match:
        grant_title, title_error = title_best_match
        if title_error:
            gen_proposal_sheet_manager.add_issue(next_row, "Title", "warning", title_error)


        # Start Date = Dates > Requested Start Date
    # End Date = Dates > Requested End Date
    # Start Date
    grant_ref_start_date = existing_data.get('Project Start Date')
    grant_gen_start_date = grant_start_date = None
    grant_db_start_date = grant_data.get('Start_Date_Req') or grant_data.get('Start_Date')
    if not grant_db_start_date:
        gen_proposal_sheet_manager.add_issue(next_row, "Project Start Date", "error", "Grant does not have a start date in database.")
        if ("OAR" or " oar " in grant_title) or (grant_sponsor_code == "JJCOAR") and grant_data.get('Status_Date'):
            grant_gen_start_date = grant_data['Status_Date']
    else:
        grant_gen_start_date = grant_db_start_date

    start_date_best_match = self.determine_best_match(grant_ref_start_date, grant_gen_start_date)
    if start_date_best_match:
        grant_start_date, start_date_error = start_date_best_match
        if start_date_error:
            gen_proposal_sheet_manager.add_issue(next_row, "Project Start Date", "warning", start_date_error)
    
    # End Date
    grant_ref_end_date = existing_data.get('Project End Date')
    grant_gen_end_date = grant_end_date =  None
    grant_db_end_date = grant_data.get('End_Date_Req') or grant_data.get('End_Date')
    if not grant_db_end_date:
        gen_proposal_sheet_manager.add_issue(next_row, "Project End Date", "error", "Grant does not have an end date in database.")
        if (("OAR" or " oar " in grant_title) or (grant_sponsor_code == "JJCOAR") and grant_data.get('Status_Date')):
            grant_gen_end_date = grant_data['Status_Date']
    else:
        grant_gen_end_date = grant_db_end_date + relativedelta(years=1)

    end_date_best_match = self.determine_best_match(grant_ref_end_date, grant_gen_end_date)
    if end_date_best_match:
        grant_end_date, end_date_error = end_date_best_match
        if end_date_error:
            gen_proposal_sheet_manager.add_issue(next_row, "Project End Date", "warning", end_date_error)

    # Missing: Proposal Type

    # Activity Type
    grant_ref_activity_type = existing_data.get('Activity Type')
    grant_gen_activity_type = grant_activity_type =  None
    grant_db_activity_type = grant_data.get('Award_Type')
    if grant_db_activity_type:
        try:
            determined_activity_type = find_closest_match(grant_db_activity_type, self.ACTIVITY_TYPES, case_sensitive=False)
            if not determined_activity_type:
                raise ValueError(f"Grant has invalid Award_Type in database: {grant_db_activity_type}")
            if determined_activity_type[1] < 90:
                gen_proposal_sheet_manager.add_issue(next_row, "Activity Type", "warning", f"Failed to find exact match for Award_Type '{grant_db_activity_type}' but is similar to '{determined_activity_type[0]}'")
            grant_gen_activity_type = determined_activity_type[0]
        except Exception as err:
            gen_proposal_sheet_manager.add_issue(next_row, "Activity Type", "error", err)
    else:
        gen_proposal_sheet_manager.add_issue(next_row, "Activity Type", "error", "Grant is missing Award_Type in database.")

    activity_type_best_match = self.determine_best_match(grant_ref_activity_type, grant_gen_activity_type)
    if activity_type_best_match:
        grant_activity_type, activity_type_error = activity_type_best_match
        if activity_type_error:
            gen_proposal_sheet_manager.add_issue(next_row, "Activity Type", "warning", activity_type_error)
    
    # Discipline
    grant_ref_discipline = existing_data.get('Discipline')
    grant_gen_discipline = grant_discipline = None
    grant_db_discipline = grant_data.get('Discipline')
    if grant_db_discipline:
        determined_discipline = find_closest_match(grant_db_discipline, self.DISCIPLINES, case_sensitive=False)
        if not determined_discipline:
            raise ValueError(f"Grant has invalid Discipline in database: {grant_db_discipline}")
        if determined_discipline[1] < 90:
            gen_proposal_sheet_manager.add_issue(next_row, "Discipline", "warning", f"Exact match for grant discipline '{grant_db_discipline}' was not found but is similar to '{determined_discipline[0]}'")
        grant_gen_discipline = determined_discipline[0]
    else:
        gen_proposal_sheet_manager.add_issue(next_row, "Discipline", "error", "Grant is missing Discipline in database.")

    # Fallback: Discipline
    grant_db_primary_dept = grant_data.get('Primary_Dept')
    if not grant_gen_discipline and grant_db_primary_dept:
        determined_discipline = find_closest_match(grant_db_primary_dept, self.DISCIPLINES, case_sensitive=False)
        if determined_discipline:
            gen_proposal_sheet_manager.add_issue(next_row, "Discipline", "warning", "Discipline was determined using Primary Dept.")
            grant_gen_discipline = determined_discipline[0]

    discipline_best_match = self.determine_best_match(grant_ref_discipline, grant_gen_discipline)
    if discipline_best_match:
        grant_discipline, discipline_error = discipline_best_match
        if discipline_error:
            gen_proposal_sheet_manager.add_issue(next_row, "Discipline", "warning", discipline_error)
    
    # Abstract
    grant_ref_abstract = existing_data.get('Abstract')
    grant_db_abstract = grant_data.get('Abstract')
    grant_abstract = None

    abstract_best_match = self.determine_best_match(grant_ref_abstract, grant_db_abstract)
    if abstract_best_match:
        grant_abstract, abstract_error = abstract_best_match
        if abstract_error:
            gen_proposal_sheet_manager.add_issue(next_row, "Abstract", "warning", abstract_error)

    grant_db_indir_dc = grant_data.get('RIndir%DC')
    grant_db_indir_per = grant_data.get('RIndir%Per')
    grant_ref_indir_cost_type = existing_data.get('Indirect Rate Cost Type')
    grant_gen_indir_cost_type = grant_indir_cost_type = None
    try:
        if grant_db_indir_dc is not None and grant_db_indir_per is not None:
            indir_dc_num = float(grant_db_indir_dc)
            indir_per_num = float(grant_db_indir_per)
            if indir_dc_num > indir_per_num:
                grant_gen_indir_cost_type = "Total Direct Costs (TDC)"
            elif indir_per_num > indir_dc_num:
                grant_gen_indir_cost_type = "Salary and Wages (SW)"
            # else:
            #     raise ValueError(f"Grant was assigned: RIndir%DC - {grant_db_indir_dc} and RIndir%Per - {grant_db_indir_per}")
        elif grant_db_indir_dc is not None:
            grant_gen_indir_cost_type = "Total Direct Costs (TDC)"
        elif grant_db_indir_per is not None:
            grant_gen_indir_cost_type = "Salary and Wages (SW)"
        # else:
        #     raise ValueError("Grant is missing Indirect Percentage in database.")
    except Exception as err:
        gen_proposal_sheet_manager.add_issue(next_row, "Indirect Rate Cost Type", "error", err)

    indir_cost_type_best_match = self.determine_best_match(grant_ref_indir_cost_type, grant_gen_indir_cost_type)
    if indir_cost_type_best_match:
        grant_indir_cost_type, indir_cost_type_error = indir_cost_type_best_match
        if indir_cost_type_error:
            gen_proposal_sheet_manager.add_issue(next_row, "Indirect Rate Cost Type", "warning", indir_cost_type_error)
    
    grant_ref_idc_rate = existing_data.get('IDC Rate')
    grant_gen_idc_rate = grant_idc_rate = None
    if grant_indir_cost_type:
        calculated_rate = 0
        if grant_indir_cost_type == "Total Direct Costs (TDC)":
            calculated_rate = float(grant_db_indir_dc)
        elif grant_indir_cost_type == "Salary and Wages (SW)":
            calculated_rate = float(grant_db_indir_per)
        grant_gen_idc_rate = round(calculated_rate * 100, 1)

    idc_rate_best_match = self.determine_best_match(grant_ref_idc_rate, grant_gen_idc_rate)
    if idc_rate_best_match:
        grant_idc_rate, idc_rate_error = idc_rate_best_match
        if idc_rate_error:
            gen_proposal_sheet_manager.add_issue(next_row, "IDC Rate", "warning", idc_rate_error)

    grant_ref_idc_cost_type_explain = existing_data.get('IDC Cost Type Explanation')
    grant_db_idc_cost_type_explain = grant_data.get('Indirect_Deviation')
    idc_cost_type_explain = None
    idc_cost_type_explain_best_match = self.determine_best_match(grant_ref_idc_cost_type_explain, grant_db_idc_cost_type_explain)
    if idc_cost_type_explain_best_match:
        idc_cost_type_explain, idc_cost_type_explain_error = idc_cost_type_explain_best_match
        if idc_cost_type_explain_error:
            gen_proposal_sheet_manager.add_issue(next_row, "IDC Cost Type Explanation", "warning", idc_cost_type_explain_error)

    # grant_total_sponsor_cost = None # Project Funds > Requested Total > Total Requested
    # grant_total_indirect_cost = None # Indirect > Requested Indirect > Total Requested
    # grant_total_direct_cost = None  # total_sponsor_cost - total_indirect_cost
    grant_num_budget_periods = len(total_data)

    grant_total_sponsor_cost = round(sum(map(lambda fund: fund.get('RAmount'), total_data)), 2)
    grant_total_indirect_cost = round(sum(map(lambda fund: fund.get('RIAmount'), rifunds_data)), 2)
    grant_total_direct_cost = round(grant_total_sponsor_cost - grant_total_indirect_cost, 2)

    # Total Cost Share - If value exists, "Cost Share Required" = Yes else No or Empty
    grant_total_cost_share = round(sum(map(lambda fund: fund.get('CSBudAmount', 0), costshare_data)))

    # Yes/No fields
    grant_yn_subrecipient = "Yes" if grant_data.get('Subcontract') else "No"
    grant_subrecipient_name = grant_data.get('Subrecipient_1')
    if grant_yn_subrecipient == "Yes" and grant_subrecipient_name is None:
        gen_proposal_sheet_manager.add_issue(next_row, "Subrecipient Names", "error", "Grant assigned Subcontract in database but is missing Subrecipients")

    grant_yn_human_subjects = "Yes" if grant_data.get('Human Subjects') else "No"
    grant_yn_animal_subjects = "Yes" if grant_data.get('Research Animals') else "No"
    grant_yn_hazard_material = "Yes" if grant_data.get('Biohazards') else "No"
    grant_yn_export_control = "Yes" if grant_data.get('Export Control') else "No"
    grant_yn_irb_approval = "Approved" if grant_data.get('IRB_Approval') else None

    grant_comments = grant_data.get('Comments')
    grant_irb_approval_date = grant_data.get('IRB_Start') if grant_yn_irb_approval else None
    
    grant_submit_date = grant_data.get('Date_Submitted')
    if not grant_submit_date:
        gen_proposal_sheet_manager.add_issue(next_row, "Submission Date", "error", "Grant is missing Date_Submitted in database.")

    grant_admin_unit_center = grant_admin_unit_name = grant_admin_unit_code = None
    if grant_db_primary_dept:
        grant_gen_admin_unit_center = grant_gen_admin_unit_name = None
        try:
            determined_center = find_closest_match(grant_db_primary_dept, list(self.CENTERS.keys()), case_sensitive=False)
            if determined_center:
                if determined_center[1] < 90:
                    gen_proposal_sheet_manager.add_issue(next_row, "John Jay Centers", "warning", f"Failed to find exact match for John Jay Center: {grant_db_primary_dept}")
                grant_gen_admin_unit_center = determined_center[0]
        except Exception as err:
            gen_proposal_sheet_manager.add_issue(next_row, "John Jay Centers", "error", err)
        
        admin_unit_center_best_match = self.determine_best_match(None, grant_gen_admin_unit_center)
        if admin_unit_center_best_match:
            grant_admin_unit_center, admin_unit_center_error = admin_unit_center_best_match
            if admin_unit_center_error:
                gen_proposal_sheet_manager.add_issue(next_row, "John Jay Centers", "warning", admin_unit_center_error)
            grant_admin_unit_name, grant_admin_unit_code = self.CENTERS[grant_admin_unit_center].values()
        
        if not grant_admin_unit_center:
            try:
                determined_admin = find_closest_match(grant_db_primary_dept, list(self.INTERNAL_ORGS), case_sensitive=False)
                if not determined_admin:
                    raise ValueError(f"Grant has invalid Primary_Dept in database: {grant_db_primary_dept}")
                if determined_admin[1] < 90:
                    gen_proposal_sheet_manager.add_issue(next_row, "Admin Unit", "warning", f"Failed to find exact match for Admin Unit: {grant_db_primary_dept}")
                grant_gen_admin_unit_name = determined_admin[0]
            except Exception as err:
                gen_proposal_sheet_manager.add_issue(next_row, "Admin Unit", "error", err)
        
        admin_unit_best_match = self.determine_best_match(existing_data.get('Admin Unit Name'), grant_gen_admin_unit_name)
        if admin_unit_best_match:
            grant_admin_unit_name, admin_unit_error = admin_unit_best_match
            if admin_unit_error:
                gen_proposal_sheet_manager.add_issue(next_row, "Admin Unit", "warning", admin_unit_error)
            grant_admin_unit_code = self.INTERNAL_ORGS[grant_admin_unit_name].get('Primary Code')
    else:
        gen_proposal_sheet_manager.add_issue(next_row, "Admin Unit", "error", "Grant is missing Primary_Dept in database.")
    
    # year_x_direct_cost = year_x_total_cost - year_x_indirect_cost
    # year_x_indirect_cost = Indirect > Requested Indirect > period_x > amount
    # year_x_total_cost = Project Funds > Requested Total > period_x > amount

    formatted_total_cost = map_yearly_cost(total_data, "RGrant_Year", "RAmount")
    formatted_indirect_cost = map_yearly_cost(rifunds_data, "RIGrant_Year", "RIAmount")
    grant_yearly_total_cost = grant_yearly_indirect_cost = grant_yearly_direct_cost = {}
    if (
        formatted_total_cost and
        formatted_indirect_cost and
        len(formatted_total_cost) == len(formatted_indirect_cost)
    ):
        grant_yearly_total_cost = determine_yearly_cost(formatted_total_cost, "Year {} Total Costs")
        grant_yearly_indirect_cost = determine_yearly_cost(formatted_indirect_cost, "Year {} Indirect Costs")
        grant_yearly_direct_cost = determine_yearly_direct_cost(formatted_total_cost, formatted_indirect_cost, "Year {} Direct Costs")

    gen_proposal_sheet_manager.append_row({
        "projectLegacyNumber": grant_pln,
        "proposalLegacyNumber": grant_id,
        "status": grant_status,
        "OAR Status": grant_db_status,      # For Staff Use
        "Proposal Legacy Number": None,
        "CUNY Campus": grant_campus,
        "Instrument Type": grant_instrument_type,
        "Sponsor": grant_sponsor_code,
        "Sponsor Name": grant_gen_sponsor_name,         # For Staff Use
        "Prime Sponsor": grant_prime_sponsor,
        "Prime Sponsor Name": grant_gen_prime_sponsor_name,       # For Staff Use
        "Title": grant_title,
        "Project Start Date": grant_start_date.date() if grant_start_date else None,
        "Project End Date": grant_end_date.date() if grant_end_date else None,
        "Proposal Type": "New",
        "Activity Type": grant_activity_type,
        "Discipline": grant_discipline,
        "Abstract": None,  # Fix bug
        "Number of Budget Periods": grant_num_budget_periods,
        "Indirect Rate Cost Type": grant_indir_cost_type,
        "IDC Rate": grant_idc_rate,
        "IDC Cost Type Explanation": idc_cost_type_explain,
        "Total Direct Costs": grant_total_direct_cost,
        "Total Indirect Costs": grant_total_indirect_cost,
        "Total Sponsor Costs": grant_total_sponsor_cost,
        **grant_yearly_total_cost,
        **grant_yearly_indirect_cost,
        **grant_yearly_direct_cost,
        "IDC Rate Less OnCampus Rate": "No",
        "Cost Share Required": "Yes" if grant_total_cost_share != 0 else "No",
        "Total Cost Share": grant_total_cost_share,
        "Reassigned Time YN": "No",
        "Reassigned Time Details": None,
        "On Site": "Yes",   # Fix
        "Off Site": "No",   # Fix
        "Subrecipient": grant_yn_subrecipient,
        "Subrecipient Names": grant_subrecipient_name,
        "Human Subjects": grant_yn_human_subjects,
        "IRB Protocol Status": grant_yn_irb_approval,
        "IRB Approval Date": grant_irb_approval_date.date() if grant_irb_approval_date else None,
        "Animal Subjects": grant_yn_animal_subjects,
        "Hazardous Materials": grant_yn_hazard_material,
        "Export Control": grant_yn_export_control,
        "Additional Comments": grant_db_status + (f" | {grant_comments}" if grant_comments else ""),
        "Submission Date": grant_submit_date.date() if grant_submit_date else None,
        "John Jay Centers": grant_admin_unit_center,
        "Admin Unit": grant_admin_unit_code,
        "Admin Unit Name": grant_admin_unit_name       # For Staff Use
    })