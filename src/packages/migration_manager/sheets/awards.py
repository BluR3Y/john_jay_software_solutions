from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .. import MigrationManager

SHEET_NAME = "Award - Template"

def determine_yearly_costs() -> list[dict]:
    pass

def safe_convert(x):
    if x == None:
        return 0
    try:
        return int(x)
    except (TypeError, ValueError):
        return 0
    
# def determine_awarded_yearly_total_cost(total_data: list):
#     total_costs = {}

#     for num_year, total_item in enumerate(sorted(total_data, key=(lambda d: int(d.get('FGrant_Year').lstrip()))), 1):
#         total_costs[f"Awarded Yr {num_year} Total Costs"] = total_item.get('FAmount')

#     return total_costs

# def determine_awarded_yearly_indirect_cost(indirect_data: list):
#     indirect_costs = {}

#     for num_year, indirect_item in enumerate(sorted(indirect_data, key=(lambda d: int(d.get('FIGrant_Year').lstrip()))), 1):
#         indirect_costs[f"Awarded Yr {num_year} Indirect Costs"] = indirect_item.get('FIAmount')

#     return indirect_costs

# def determine_awarded_yearly_direct_cost(yearly_total_costs, yearly_indirect_costs):
#     direct_costs = {}

#     for num_year in range(1, max(len(yearly_total_costs), len(yearly_indirect_costs)) + 1):
#         year_total_cost = yearly_total_costs.get(f"Awarded Yr {num_year} Total Costs", 0)
#         year_indirect_cost = yearly_indirect_costs.get(f"Awarded Yr {num_year} Indirect Costs", 0)
#         direct_costs[f"Awarded Yr {num_year} Direct Costs"] = round(year_total_cost - year_indirect_cost, 2)

#     return direct_costs

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

def awards_sheet_append(
    self: "MigrationManager",
    grant_data: dict,
    total_data: list[dict],
    rifunds_data: list[dict],
    dates_data: list[dict],
    costshare_data: list[dict],
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
    
    grant_num_budget_periods = proposal_sheet_data.get('Number of Budget Periods')
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
    grant_has_off_site = proposal_sheet_data.get('Off Site')
    grant_has_subrecipient = proposal_sheet_data.get('Subrecipient')
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
    grant_total_awarded_indirect_cost = round(sum(map(lambda fund: fund.get('FIAmount'), fifunds_data)), 2)
    grant_total_expected_amount = round(sum(map(lambda fund: fund.get('FAmount'), ffunds_data)), 2)
    grant_total_awarded_direct_cost = round(grant_total_expected_amount - grant_total_awarded_indirect_cost, 2)

    # Subrecipient Names - Separated by '|'. Ex: James | Luna

    # awarded_yr_x_direct_cost = awarded_yr_x_total_cost - awarded_yr_x_indirect_cost
    # awarded_yr_x_indirect_cost = Indirect > Funded Indirect > period_x > Amount
    # awarded_yr_x_total_cost = project Funds > Funded Total > period_x > Amount

    # grant_awarded_yearly_total_cost = determine_awarded_yearly_total_cost(ffunds_data)
    # grant_awarded_yearly_indirect_cost = determine_awarded_yearly_indirect_cost(fifunds_data)
    # grant_awarded_yearly_direct_cost = determine_awarded_yearly_direct_cost(grant_awarded_yearly_total_cost, grant_awarded_yearly_indirect_cost)
    formatted_total_cost = map_yearly_cost(ffunds_data, "FGrant_Year", "FAmount")
    formatted_indirect_cost = map_yearly_cost(fifunds_data, "FIGrant_Year", "FIAmount")
    grant_awarded_yearly_total_cost = grant_awarded_yearly_indirect_cost = grant_awarded_yearly_direct_cost = {}
    if (
        formatted_total_cost and
        formatted_indirect_cost and
        len(formatted_total_cost) == len(formatted_indirect_cost)
    ):
        grant_awarded_yearly_total_cost = determine_yearly_cost(formatted_total_cost, "Awarded Yr {} Total Costs")
        grant_awarded_yearly_direct_cost = determine_yearly_cost(formatted_indirect_cost, "Awarded Yr {} Indirect Costs")
        grant_awarded_yearly_direct_cost = determine_yearly_direct_cost(formatted_total_cost, formatted_indirect_cost, "Awarded Yr {} Direct Costs")
        

# def determine_awarded_yearly_total_cost(total_data: list):
#     total_costs = {}

#     for num_year, total_item in enumerate(sorted(total_data, key=(lambda d: int(d.get('FGrant_Year').lstrip()))), 1):
#         total_costs[f"Awarded Yr {num_year} Total Costs"] = total_item.get('FAmount')

#     return total_costs

# def determine_awarded_yearly_indirect_cost(indirect_data: list):
#     indirect_costs = {}

#     for num_year, indirect_item in enumerate(sorted(indirect_data, key=(lambda d: int(d.get('FIGrant_Year').lstrip()))), 1):
#         indirect_costs[f"Awarded Yr {num_year} Indirect Costs"] = indirect_item.get('FIAmount')

#     return indirect_costs

# def determine_awarded_yearly_direct_cost(yearly_total_costs, yearly_indirect_costs):
#     direct_costs = {}

#     for num_year in range(1, max(len(yearly_total_costs), len(yearly_indirect_costs)) + 1):
#         year_total_cost = yearly_total_costs.get(f"Awarded Yr {num_year} Total Costs", 0)
#         year_indirect_cost = yearly_indirect_costs.get(f"Awarded Yr {num_year} Indirect Costs", 0)
#         direct_costs[f"Awarded Yr {num_year} Direct Costs"] = round(year_total_cost - year_indirect_cost, 2)

#     return direct_costs

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
        "Award Notice Received": award_notice_recieved.date() if award_notice_recieved else None,
        "Project Start Date": grant_start_date.date() if grant_start_date else None,
        "Project End Date": grant_end_date.date() if grant_end_date else None,
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
        **grant_awarded_yearly_direct_cost,
        **grant_awarded_yearly_indirect_cost,
        **grant_awarded_yearly_total_cost,
        "Cost Share Required": "Yes" if grant_total_cost_share != 0 else "No",
        "Total Cost Share": grant_total_cost_share,
        "Human Subjects": grant_has_human_subjects,
        "IRB Protocol Status": grant_has_irb_approval,
        "IRB Approval Date": grant_irb_approval_date,
        "Animal Subjects": grant_has_animal_subjects,
        "Hazardous Materials": grant_has_hazard_material,
        "On Site": grant_has_on_site,
        "Off Site": grant_has_off_site,
        "Subrecipient": grant_has_subrecipient,
        "Subrecipient Names": "",
        "Export Control": grant_has_export_control,
        "Award Type": "Funded Award"
    })