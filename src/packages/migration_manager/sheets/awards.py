import pandas as pd
import numpy as np

from datetime import datetime
from dateutil.relativedelta import relativedelta

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Only imported for type checking
    from packages.migration_manager import MigrationManager
    
SHEET_NAME = "Award - Template"

def safe_convert(x):
    if x == None:
        return 0
    try:
        return int(x)
    except (TypeError, ValueError):
        return 0

def awards_sheet_append(
        self: "MigrationManager",
        grant_data,
        total_data,
        rifunds_data,
        dates_data, 
        costshare_data,
        ffunds_data,
        fifunds_data
    ):
    gt_manager = self.generated_template_manager
    ft_manager = self.feedback_template_manager
    next_row = gt_manager.df[SHEET_NAME].shape[0] + 1
    
    grant_id = grant_data['Grant_ID']
    grant_pln = grant_data['Project_Legacy_Number']
    
    existing_data = ft_manager.find(SHEET_NAME, {"projectLegacyNumber": grant_pln}, return_one=True, to_dict='records') or {}
    proposal_sheet_entry_ref = gt_manager.find("Proposal - Template", { "proposalLegacyNumber": grant_id }, return_one=True)
    proposal_sheet_entry = gt_manager.formatDF(proposal_sheet_entry_ref).to_dict() if not proposal_sheet_entry_ref.empty else {}

    grant_status = grant_data['Status']
    grant_oar = proposal_sheet_entry.get('status')
    if not grant_oar:
        existing_oar = existing_data.get('status')
        if existing_oar:
            grant_oar = existing_oar
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 2, "warning", "OAR status was determined using feedback file.")
        
    grant_primary_college = proposal_sheet_entry.get('CUNY Campus')
    if not grant_primary_college:
        existing_college = existing_data.get('CUNY Campus')
        if existing_college:
            grant_primary_college = existing_college
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 4, 'warning', "Primary College was determined using feedback file.")
    
    grant_instrument_type = proposal_sheet_entry.get('Instrument Type')
    if not grant_instrument_type:
        existing_instrument = existing_data.get('Instrument Type')
        if existing_instrument:
            grant_instrument_type = existing_instrument
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 7, 'warning', "Instrument Type was determined using feedback file.")
            
            proposal_sheet_entry_ref = gt_manager.update_cell("Feedback Generator", "Proposal - Template", proposal_sheet_entry_ref, {"Instrument Type": existing_instrument})
            # Add comment in proposal record regarding found instrument
            
            
    grant_sponsor = None
    grant_sponsor_code = proposal_sheet_entry.get('Sponsor')
    if not grant_sponsor_code:
        existing_sponsor_code = existing_data.get('Sponsor Code')
        if existing_sponsor_code:
            grant_sponsor_code = existing_sponsor_code
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 8, 'warning', "Sponsor was determined using feedback file.")
    # Retrieve sponsor name
    
    grant_prime_sponsor = proposal_sheet_entry.get('Prime Sponsor')
    if not grant_prime_sponsor:
        existing_prime_sponsor = existing_data.get('Prime Sponsor')
        if existing_prime_sponsor:
            grant_prime_sponsor = existing_prime_sponsor
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 12, 'warning', "Prime sponsor was determined using feedback file.")
    
    grant_award_no = grant_data['Award_No']
    if not grant_award_no:
        existing_award_no = existing_data.get('Sponsor Award Number')
        if existing_award_no:
            grant_award_no = existing_award_no
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 10, 'warning', "Award Number was determined using feedback file.")
            
    grant_title = proposal_sheet_entry.get('Title')
    if not grant_title:
        existing_title = existing_data.get('Title')
        if existing_title:
            grant_title = existing_title
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 18, 'warning', "Title was determined using feedback file.")
    
    award_notice_date = None
    for date_obj in sorted(dates_data, key=lambda d: safe_convert(d.get('DatePeriod'))):
        status_date = date_obj.get('StatusDate')
        if status_date is not None:
            award_notice_date = status_date
            break
    
    if not award_notice_date:
        existing_notice_date = existing_data.get('Award Notice Received')
        if existing_notice_date:
            award_notice_date = existing_notice_date
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 18, 'warning', "Status Date was determined using feedback file.")
            
    if award_notice_date and grant_sponsor_code.lower() == "jjcoar":
        if not proposal_sheet_entry.get('Project Start Date'):
            proposal_sheet_entry_ref = gt_manager.update_cell("Feedback Generator", "Proposal - Template", proposal_sheet_entry_ref, {"Project Start Date":award_notice_date})
        if not proposal_sheet_entry.get('Project End Date'):
            proposal_sheet_entry_ref = gt_manager.update_cell("Feedback Generator", "Proposal - Template", proposal_sheet_entry_ref, {"Project End Date":award_notice_date})
        
            
    project_start_date = proposal_sheet_entry.get('Project Start Date')
    if not project_start_date:
        existing_start_date = existing_data.get('Project Start Date')
        if existing_start_date:
            project_start_date = existing_start_date
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 18, 'warning', "Start Date was determined using feedback file.")
    
    project_end_date = proposal_sheet_entry.get('Project End Date')
    if not project_end_date:
        existing_end_date = existing_data.get('Project End Date')
        if existing_end_date:
            project_end_date = existing_end_date
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 30, 'warning', "End Date was determined using feedback file.")
        
    program_name = grant_data['Program_Type']
    if not program_name:
        existing_name = existing_data.get('Program Name')
        if existing_name:
            program_name = existing_name
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 50, 'warning', "Program Name was determined using feedback file.")
    
    grant_activity_type = proposal_sheet_entry.get('Activity Type')
    if not grant_activity_type:
        existing_activity = existing_data.get('Activity Type')
        if existing_activity:
            grant_activity_type = existing_activity
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 20, 'warning', "Activity Type was determined using feedback file.")
            
    if grant_activity_type and not proposal_sheet_entry.get('Activity Type'):
        proposal_sheet_entry_ref = gt_manager.update_cell("Feedback Generator", "Proposal - Template", proposal_sheet_entry_ref, {"Activity Type":grant_activity_type})
            
    grant_discipline = proposal_sheet_entry.get('Discipline')
    if not grant_discipline:
        existing_discipline = existing_data.get('Discipline')
        if existing_discipline:
            grant_discipline = existing_discipline
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 25, 'warning', "Discipline was determined using feedback file.")
            
    grant_abstract = proposal_sheet_entry.get('Abstract')
    # if not grant_abstract:
    #     existing_abstract = existing_data.get('Abstract')
    #     if existing_abstract:
    #         grant_abstract = existing_abstract
    #         gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 18, 'warning', "Abstract was determined using feedback file.")
    
    award_legacy_no = grant_data['Award_No']
    if not award_legacy_no:
        existing_legacy_no = existing_data.get('Award Legacy Number')
        if existing_legacy_no:
            award_legacy_no = existing_legacy_no
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 20, 'warning', "Award Legacy Number was determined using feedback file.")
    
    grant_admin_unit_name = proposal_sheet_entry.get('Admin Unit Name')
    if not grant_admin_unit_name:
        existing_unit_name = existing_data.get('Admin Unit Name')
        if existing_unit_name:
            grant_admin_unit_name = existing_unit_name
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 20, 'warning', "Admin Unit Name was determined using feedback file.")
            
    grant_admin_unit_code = proposal_sheet_entry.get('Admin Unit Code')
    if not grant_admin_unit_code:
        existing_unit_code = existing_data.get('Admin Unit Code')
        if existing_unit_code:
            grant_admin_unit_code = existing_unit_code
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 30, 'warning', "Admin Unit Code was determined using feedback file.")
    
    grant_admin_unit_center = proposal_sheet_entry.get('John Jay Centers')
    if not grant_admin_unit_center:
        existing_unit_center = existing_data.get('John Jay Centers')
        if existing_unit_center:
            grant_admin_unit_center = existing_unit_center
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 59, 'warning', "Admin Unit Center was determined using feedback file.")
            
    # Budgeting --------------------------------------------------------
            
    grant_num_budget_periods = proposal_sheet_entry.get('Number of Budget Periods')
    if not grant_num_budget_periods:
        existing_num_budget_periods = existing_data.get('Number of Budget Periods')
        if existing_num_budget_periods:
            grant_num_budget_periods = existing_num_budget_periods
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 49, 'warning', "Number of periods was determined using feedback file.")
    
    grant_rate_cost_type = proposal_sheet_entry.get('Indirect Rate Cost Type')
    if not grant_rate_cost_type:
        existing_rate_cost_type = existing_data.get('Indirect Rate Cost Type')
        if existing_rate_cost_type:
            grant_rate_cost_type = existing_rate_cost_type
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 36, 'warning', "Cost Type was determined using feedback file")
    
    grant_idc_rate = proposal_sheet_entry.get('IDC Rate Less OnCampus Rate')
    if not grant_idc_rate:
        if grant_rate_cost_type:
            grant_idc_rate = round((float(grant_data['RIndir%DC']) if grant_rate_cost_type == "Total Direct Costs (TDC)" else (float(grant_data['RIndir%Per']) if grant_rate_cost_type == "Salary and Wages (SW)" else 0)) * 100, 1)
        elif existing_data.get('IDC Rate'):
            grant_idc_rate = existing_data.get('IDC Rate')
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 37, 'warning', "IDC Rate was determined using feedback file")

    grant_idc_cost_type_explain = grant_data['Indirect_Deviation']
    if not grant_idc_cost_type_explain:
        existing_cost_explain = existing_data.get('IDC Cost Type Explain')
        if existing_cost_explain:
            grant_idc_cost_type_explain = existing_cost_explain
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 38, 'warning', "Cost Type Explaination was determined using feedback file.")
    
    grant_total_expected_amount = round(sum(map(lambda fund: fund['RAmount'], total_data)))
    grant_total_awarded_indirect_amount = round(sum(map(lambda fund: fund['RIAmount'], rifunds_data)))
    grant_total_awarded_direct_amount = round(grant_total_expected_amount - grant_total_awarded_indirect_amount)
    
    first_year_indirect_costs = 0
    if rifunds_data:
        first_fund = min(rifunds_data, key=lambda x: safe_convert(x["RIGrant_Year"]))
        first_year_indirect_costs = round(first_fund['RIAmount'])
    first_year_total_costs = 0
    if total_data:
        first_fund = min(total_data, key=lambda x: safe_convert(x['RGrant_Year']))
        first_year_total_costs = round(first_fund['RAmount'])
    first_year_direct_costs = round(first_year_total_costs - first_year_indirect_costs)
    
    first_year_awarded_total_costs = round(sum(map(lambda fund: safe_convert(fund['FAmount']), ffunds_data)))
    first_year_awarded_indirect_costs = round(sum(map(lambda fund: safe_convert(fund['FIAmount']), fifunds_data)))
    first_year_awarded_direct_costs = round(first_year_awarded_total_costs - first_year_awarded_indirect_costs)
    
    grant_total_cost_share = round(sum(map(lambda fund: safe_convert(fund['CSBudAmount']), costshare_data)))
    
    grant_has_subrecipient = proposal_sheet_entry.get('Subrecipient')
    if not grant_has_subrecipient:
        existing_subrecipient = existing_data.get('Subrecipient')
        if existing_subrecipient:
            grant_has_subrecipient = existing_subrecipient
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 50, 'warning', "Subrecipient was determined using feedback file.")
    
    grant_has_human_subjects = proposal_sheet_entry.get('Human Subjects')
    if not grant_has_human_subjects:
        existing_human_subjects = existing_data.get('Human Subjects')
        if existing_human_subjects:
            grant_has_human_subjects = existing_human_subjects
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 50, 'warning', "Human Subjects was determined using feedback file.")
            
    grant_has_animal_subjects = proposal_sheet_entry.get('Animal Subjects')
    if not grant_has_animal_subjects:
        existing_animal_subjects = existing_data.get('Animal Subjects')
        if existing_animal_subjects:
            grant_has_animal_subjects = existing_animal_subjects
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 50, 'warning', "Animal Subjects was determined using feedback file.")
            
    grant_has_subrecipient = proposal_sheet_entry.get('Subrecipient')
    if not grant_has_subrecipient:
        existing_subrecipient = existing_data.get('Subrecipient')
        if existing_subrecipient:
            grant_has_subrecipient = existing_subrecipient
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 50, 'warning', "Subrecipient was determined using feedback file.")
            
    grant_has_hazard_material = proposal_sheet_entry.get('Hazardous Materials')
    if not grant_has_hazard_material:
        existing_hazard_material = existing_data.get('Hazardous Materials')
        if existing_hazard_material:
            grant_has_hazard_material = existing_hazard_material
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 50, 'warning', "Hazardous Materials was determined using feedback file.")
            
    grant_has_export_control = proposal_sheet_entry.get('Export Control')
    if not grant_has_export_control:
        existing_export_control = existing_data.get('Export Control')
        if existing_export_control:
            grant_has_export_control = existing_export_control
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 50, 'warning', "Export Control was determined using feedback file.")
            
    grant_has_irb_approval = proposal_sheet_entry.get('IRB Protocol Status')
    if not grant_has_irb_approval:
        existing_irb_approval = existing_data.get('IRB Protocol Status')
        if existing_irb_approval:
            grant_has_irb_approval = existing_irb_approval
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 50, 'warning', "IRB Protocol Status was determined using feedback file.")
    
    grant_irb_approval_date = proposal_sheet_entry.get('IRB Approval Date')
    if not grant_irb_approval_date:
        existing_irb_approval_date = existing_data.get('IRB Approval Date')
        if existing_irb_approval_date:
            grant_irb_approval_date = existing_irb_approval_date
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 50, 'warning', "IRB Approval Date was determined using feedback file.")
    
    self.generated_template_manager.append_row(SHEET_NAME, {
        "projectLegacyNumber": grant_pln,
        "proposalLegacyNumber": grant_id,
        "awardLegacyNumber": f"{grant_id}-award",
        "status": grant_status,
        "OAR Status": grant_oar,
        "modificationNumber": 0,
        "CUNY Campus": grant_primary_college,
        "Instrument Type": grant_instrument_type,
        "Sponsor": grant_sponsor,
        "Sponsor Code": grant_sponsor_code,
        "Sponsor Award Number": grant_award_no,
        "Prime Sponsor": grant_prime_sponsor,
        "Title": grant_title,
        "Award Notice Received": award_notice_date,
        "Project Start Date": project_start_date,
        "Project End Date": project_end_date,
        "Program Name": program_name,
        "Activity Type": grant_activity_type,
        "Admin Unit Name": grant_admin_unit_name,
        "Admin Unit": grant_admin_unit_code,
        "John Jay Centers": grant_admin_unit_center,
        "Discipline": grant_discipline,
        "Abstract": "",
        "Award Legacy Number": award_legacy_no,
        "Number of Budget Periods": grant_num_budget_periods,
        "Indirect Rate Cost Type": grant_rate_cost_type,
        "IDC Rate": grant_idc_rate,
        "IDC Cost Type Explanation": grant_idc_cost_type_explain,
        "Total Awarded Direct Costs": grant_total_awarded_direct_amount,
        "Total Awarded Indirect Costs": grant_total_awarded_indirect_amount,
        "Total Expected Amount": grant_total_expected_amount,
        "Yr 1 Direct Costs": first_year_direct_costs,
        "Year 1 Indirect Costs": first_year_indirect_costs,
        "Year 1 Total Costs": first_year_total_costs,
        "Awarded Yr 1 Direct Costs": first_year_awarded_direct_costs,
        "Awarded Yr 1 Indirect Costs": first_year_awarded_indirect_costs,
        "Awarded Yr 1 Total Costs": first_year_awarded_total_costs,
        "Total Cost Share": grant_total_cost_share,
        "Human Subjects": grant_has_human_subjects,
        "IRB Protocol Status": grant_has_irb_approval,
        "IRB Approval Date": grant_irb_approval_date,    # leave blank, requires value in column DK
        "Animal Subjects": grant_has_animal_subjects,
        "Hazardous Materials": grant_has_hazard_material,
        "On Site": "",
        "Off Site": "",
        "Subrecipient": grant_has_subrecipient,
        "Export Control": grant_has_export_control
    })