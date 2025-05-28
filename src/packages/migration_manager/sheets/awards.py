from typing import TYPE_CHECKING, Union
import traceback
from datetime import datetime, date

if TYPE_CHECKING:
    from .. import MigrationManager

SHEET_NAME = "Award - Template"

def safe_convert(x):
    if x == None:
        return 0
    try:
        return int(x)
    except (TypeError, ValueError):
        return 0

def map_yearly_cost(cost_data: list[dict], period_key: str, amount_key: str) -> list[float]:
    period_data = {}
    for item in cost_data:
        # period = item.get(period_key, f"{len(period_data.keys()) + 1}")
        period = item.get(period_key) or f"{len(period_data.keys()) + 1}".lstrip('0')
        if period is period_data:
            return None
        period_data[int(period)] = item.get(amount_key) or 0
    
    if len(period_data) > 1:
        for idx in [period_data.keys()][1:]:
            if not period_data.get(idx - 1):
                return None

    return list(period_data.values())

        # grant_yearly_total_cost = determine_yearly_cost(formatted_total_cost, "Year {} Total Costs")
        # grant_yearly_indirect_cost = determine_yearly_cost(formatted_indirect_cost, "Year {} Indirect Costs")
        # grant_yearly_direct_cost = determine_yearly_direct_cost(formatted_total_cost, formatted_indirect_cost, "Year {} Direct Costs")

def determine_yearly_cost(total_costs: list, indirect_costs: list):
    yearly_cost = {}
    for index in range(len(total_costs)):
        period_total_cost = round(total_costs[index], 2)
        period_indirect_cost = round(indirect_costs[index], 2)
        period_direct_cost = round(period_total_cost - period_indirect_cost, 2)
        if period_direct_cost < 0:
            return {}

        yearly_cost[f"Awarded Yr {index + 1} Total Costs"] = period_total_cost
        yearly_cost[f"Awarded Yr {index + 1} Indirect Costs"] = period_indirect_cost
        yearly_cost[f"Awarded Yr {index + 1} Direct Costs"] = period_direct_cost

    return yearly_cost

def format_date(date_obj: Union[None, datetime, date]):
    if isinstance(date_obj, datetime):
        return date_obj.date()
    elif isinstance(date_obj, date):
        return date_obj
    return

def awards_sheet_append(
    self: "MigrationManager",
    grant_data: dict,
    dates_data: list[dict],
    ffunds_data: list[dict],
    fifunds_data: list[dict]
):
    grant_id = grant_data.get('Grant_ID')
    grant_pln = grant_data.get('Project_Legacy_Number')

    # Current Sheet Manager
    gen_awards_sheet_manager = self.generated_wb_manager[SHEET_NAME]
    next_row = gen_awards_sheet_manager.df.shape[0]
    
    # Previous Version Sheet Manager
    ref_awards_sheet_manager = self.reference_wb_manager[SHEET_NAME]
    # Current Grant Previous Award Data
    existing_award_sheet_data_ref = ref_awards_sheet_manager.find({ "projectLegacyNumber": grant_pln }, return_one=True)
    existing_award_sheet_data = existing_award_sheet_data_ref.to_dict() if existing_award_sheet_data_ref is not None else {}

    # Projects Sheet Manager
    gen_projects_sheet_manager = self.generated_wb_manager["Project - Template"]
    # Current Grant Project Data
    project_sheet_data_ref = gen_projects_sheet_manager.find({ "projectLegacyNumber": grant_pln }, return_one=True)
    project_sheet_data = project_sheet_data_ref.to_dict() if project_sheet_data_ref is not None else {}

    # Proposals Sheet Manager
    gen_proposals_sheet_manager = self.generated_wb_manager["Proposal - Template"]
    # Current Grant Proposal Data
    proposal_sheet_data_ref = gen_proposals_sheet_manager.find({ "projectLegacyNumber": grant_pln }, return_one=True)
    proposal_sheet_data = proposal_sheet_data_ref.to_dict() if proposal_sheet_data_ref is not None else {}
    
    grant_status = project_sheet_data.get('status')
    grant_campus = proposal_sheet_data.get('CUNY Campus')
    grant_instrument_type = proposal_sheet_data.get('Instrument Type')
    grant_sponsor = proposal_sheet_data.get('Sponsor')
    
    grant_prime_sponsor = proposal_sheet_data.get('Prime Sponsor')
    grant_title = proposal_sheet_data.get('Title')
    
    grant_start_date = grant_data.get('Start_Date') or proposal_sheet_data.get('Project Start Date')
    grant_end_date = grant_data.get('End_Date') or proposal_sheet_data.get('Project End Date')
    
    grant_proposal_type = proposal_sheet_data.get('Proposal Type')
    grant_activity_type = proposal_sheet_data.get('Activity Type')
    
    grant_admin_unit_center = proposal_sheet_data.get('John Jay Centers')
    grant_admin_unit = proposal_sheet_data.get('Admin Unit')
    grant_discipline = proposal_sheet_data.get('Discipline')
    grant_abstract = proposal_sheet_data.get('Abstract')
    
    # grant_num_budget_periods = safe_convert(proposal_sheet_data.get('Number of Budget Periods'))
    grant_idc_rate = proposal_sheet_data.get('IDC Rate')
    grant_indirect_rate_cost_type = proposal_sheet_data.get('Indirect Rate Cost Type')
    idc_cost_type_explain = proposal_sheet_data.get('IDC Cost Type Explanation')
    grant_total_direct_cost = proposal_sheet_data.get('Total Direct Costs')
    grant_total_indirect_cost = proposal_sheet_data.get('Total Indirect Costs')
    grant_total_sponsor_cost = proposal_sheet_data.get('Total Sponsor Costs')
    grant_total_cost_share = proposal_sheet_data.get('Total Cost Share')

    grant_has_human_subjects = proposal_sheet_data.get('Human Subjects')
    grant_has_irb_approval = proposal_sheet_data.get('IRB Protocol Status')
    grant_irb_approval_date = proposal_sheet_data.get('IRB Approval Date')
    grant_has_animal_subjects = proposal_sheet_data.get('Animal Subjects')
    grant_has_hazard_material = proposal_sheet_data.get('Hazardous Materials')
    grant_has_on_site = proposal_sheet_data.get('On Site')
    grant_on_site_location = proposal_sheet_data.get('On Site Location')
    grant_has_off_site = proposal_sheet_data.get('Off Site')
    grant_off_site_location = proposal_sheet_data.get('Off Site Location')
    grant_has_subrecipient = proposal_sheet_data.get('Subrecipient')
    grant_subrecipient_names = proposal_sheet_data.get('Subrecipient Names')
    grant_has_export_control = proposal_sheet_data.get('Export Control')


    award_notice_recieved = None
    for date_obj in sorted(dates_data, key=lambda d: safe_convert(d.get('DatePeriod'))):
        status_date = date_obj.get('StatusDate')
        if status_date is not None:
            award_notice_recieved = status_date
            break

    grant_program_name = grant_data.get('Program_Type')

    award_legacy_no = None
    grant_ref_award_legacy_no = existing_award_sheet_data.get('Award Legacy Number')
    grant_db_award_legacy_no = grant_data.get('Award_No')
    # if not grant_db_award_legacy_no:
    #     gen_awards_sheet_manager.add_issue(next_row, "Award Legacy Number", "error", "Grant is missing Award_No in database.")
    
    award_legacy_no_best_match = self.determine_best_match(grant_ref_award_legacy_no, grant_db_award_legacy_no)
    if award_legacy_no_best_match:
        award_legacy_no, award_legacy_no_error = award_legacy_no_best_match
        if award_legacy_no_error:
            gen_awards_sheet_manager.add_issue(next_row, "Award Legacy Number", "warning", award_legacy_no_error)

    
    # Total Awarded Indirect Costs = Indirect > Funded Indirect > Total Funded
    # Total Expected Amount = Project Funds > Funded Total > Total Funded
    # Total Awarded Direct Costs = Expected - Indirect
    grant_total_awarded_indirect_cost = round(sum(map(lambda fund: (fund.get('FIAmount') or 0), fifunds_data)), 2)
    grant_total_expected_amount = round(sum(map(lambda fund: (fund.get('FAmount') or 0), ffunds_data)), 2)
    grant_total_awarded_direct_cost = round(grant_total_expected_amount - grant_total_awarded_indirect_cost, 2)

    # Subrecipient Names - Separated by '|'. Ex: James | Luna

    # awarded_yr_x_direct_cost = awarded_yr_x_total_cost - awarded_yr_x_indirect_cost
    # awarded_yr_x_indirect_cost = Indirect > Funded Indirect > period_x > Amount
    # awarded_yr_x_total_cost = project Funds > Funded Total > period_x > Amount

    formatted_total_cost = map_yearly_cost(ffunds_data, "FGrant_Year", "FAmount")
    formatted_indirect_cost = map_yearly_cost(fifunds_data, "FIGrant_Year", "FIAmount")
    grant_awarded_yearly_costs = {}
    if (
        formatted_total_cost and
        formatted_indirect_cost and
        len(formatted_total_cost) == len(formatted_indirect_cost)
    ):
        try:
            grant_awarded_yearly_costs = determine_yearly_cost(formatted_total_cost, formatted_indirect_cost)
        except Exception as err:
            self.generated_wb_manager["Errors"].append_row({
                    "Grant_ID": grant_id,
                    "Sheet": "Awards - Template",
                    "Issue": f"Error while computing yearly costs to awards sheet: {err}",
                    "Traceback": traceback.format_exc()
                })
    
    grant_num_budget_periods = len(formatted_total_cost)

    grant_requested_yearly_costs = {}
    if grant_num_budget_periods:
        for year_num in range(1, 11):
            # direct_cost_str = f"Year {year_num} Direct Costs"
            # indirect_cost_str = f"Year {year_num} Indirect Costs"
            # total_cost_str = f"Year {year_num} Total Costs"
            # grant_requested_yearly_costs[direct_cost_str] = proposal_sheet_data.get(direct_cost_str)
            # grant_requested_yearly_costs[indirect_cost_str] = proposal_sheet_data.get(indirect_cost_str)
            # grant_requested_yearly_costs[total_cost_str] = proposal_sheet_data.get(total_cost_str)
            period_direct_cost = proposal_sheet_data.get(f"Year {year_num} Direct Costs")
            period_indirect_cost = proposal_sheet_data.get(f"Year {year_num} Indirect Costs")
            period_total_cost = proposal_sheet_data.get(f"Year {year_num} Total Costs")
            if period_direct_cost and period_indirect_cost and period_total_cost:
                grant_requested_yearly_costs[f"Year {year_num} Direct Costs"] = period_direct_cost
                grant_requested_yearly_costs[f"Year {year_num} Indirect Costs"] = period_indirect_cost
                grant_requested_yearly_costs[f"Year {year_num} Total Costs"] = period_total_cost
        
    # formatted_total_cost = map_yearly_cost(total_data, "RGrant_Year", "RAmount")
    # formatted_indirect_cost = map_yearly_cost(rifunds_data, "RIGrant_Year", "RIAmount")
    # grant_yearly_costs = {}
    # if (
    #     formatted_total_cost and
    #     formatted_indirect_cost and
    #     len(formatted_total_cost) == len(formatted_indirect_cost)
    # ):
    #     try:
    #         grant_yearly_costs = determine_yearly_cost(formatted_total_cost, formatted_indirect_cost)
    #     except Exception as err:
    #         self.generated_wb_manager["Errors"].append_row({
    #                 "Grant_ID": grant_id,
    #                 "Sheet": "Proposal - Template",
    #                 "Issue": f"Error while computing yearly costs to proposals sheet: {err}",
    #                 "Traceback": traceback.format_exc()
    #             })

    gen_awards_sheet_manager.append_row({
        "projectLegacyNumber": grant_pln,
        "awardLegacyNumber": f"{grant_id}-award",
        "status": grant_status,
        "modificationNumber": 0,
        "CUNY Campus": grant_campus,
        "Instrument Type": grant_instrument_type,
        "Sponsor": grant_sponsor,
        "Sponsor Award Number": "",
        "Prime Sponsor": grant_prime_sponsor,
        "Prime Sponsor Award Number": "",
        "Title": grant_title,
        "Award Notice Received": format_date(award_notice_recieved),
        "Project Start Date": format_date(grant_start_date),
        "Project End Date": format_date(grant_end_date),
        "Program Name": grant_program_name,
        "Proposal Type": grant_proposal_type,
        "Activity Type": grant_activity_type,
        "John Jay Centers": grant_admin_unit_center,
        "Admin Unit": grant_admin_unit,
        "Discipline": grant_discipline,
        "Abstract": grant_abstract,
        "Award Legacy Number": award_legacy_no,
        "Account Legacy Number": grant_data.get('RF_Account'),
        "Number of Budget Periods": grant_num_budget_periods,
        "Indirect Rate Cost Type": grant_indirect_rate_cost_type,
        "IDC Rate": grant_idc_rate,
        "IDC Cost Type Explanation": idc_cost_type_explain,
        "Total Direct Costs": grant_total_direct_cost,
        "Total Indirect Costs": grant_total_indirect_cost,
        "Total Sponsor Costs": grant_total_sponsor_cost,
        "Total Awarded Direct Costs": grant_total_awarded_direct_cost,
        "Total Awarded Indirect Costs": grant_total_awarded_indirect_cost,
        "Total Expected Amount": grant_total_expected_amount,
        **grant_awarded_yearly_costs,
        **grant_requested_yearly_costs,
        "Cost Share Required": "Yes" if grant_total_cost_share != 0 else "No",
        "Total Cost Share": grant_total_cost_share,
        "Human Subjects": grant_has_human_subjects,
        "IRB Protocol Status": grant_has_irb_approval,
        "IRB Approval Date": grant_irb_approval_date,
        "Animal Subjects": grant_has_animal_subjects,
        "Hazardous Materials": grant_has_hazard_material,
        "On Site": grant_has_on_site,
        "On Site Location": grant_on_site_location,
        "Off Site": grant_has_off_site,
        "Off Site Location": grant_off_site_location,
        "Subrecipient": grant_has_subrecipient,
        "Subrecipient Names": grant_subrecipient_names,
        "Export Control": grant_has_export_control,
        "Award Type": "Funded Award"
    })