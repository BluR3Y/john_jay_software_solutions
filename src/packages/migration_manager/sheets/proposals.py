from typing import TYPE_CHECKING
from modules.utils import find_closest_match, extract_titles
from datetime import datetime
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    # Only imported for type checking
    from packages.migration_manager import MigrationManager

SHEET_NAME = "Proposal - Template"

ACTIVITY_FALLBACK_ASSOCIATIONS = {
    'Research': 'Research on Campus',
    'Conference': 'General and Administrative Purpose on Campus',
    'Other': 'Other Institutional Activity',
    'Training': 'Instruction on Campus',
    'Course Development': 'Experimental Development Research on Campus Experimental',
    'Equipment': 'Equipment on Campus',
    'Other - Center Development': 'Other Sponsored Activity on Campus',
    'Program Development': 'Experimental Development Research on Campus Experimental',
    'Research/Training': 'Research Training on Campus',
    'Student Support': 'Fellowship'
}

# def determine_instrument_type(instance, award_type):
#     valid_types = instance.INSTRUMENT_TYPES
#     type_letter = None
#     type_title = None
#     if ('-' in award_type):
#         type_letter, type_title = award_type.split('-')
#     else:
#         type_title = award_type

#     for type_name, association in valid_types.items():
#         if type_letter in association.keys():
#             return type_name
#         closest_valid_type = find_closest_match(type_title, [str(item) for item in association.values()], case_sensitive=False)
#         if closest_valid_type:
#             return type_name
def determine_instrument_type(instance, type):
    valid_types = instance.INSTRUMENT_TYPES
    type_letter = None
    type_title = None
    if ('-' in type):
        type_letter, type_title = type.split('-')
    else:
        type_title = type

    closest_valid_type = find_closest_match(type_title, valid_types, case_sensitive=False, threshold=85)
    return closest_valid_type
    
def determine_sponsor(instance, sponsor):    
    all_orgs = {
        **instance.ORGANIZATIONS['existing_external_orgs'],
        **instance.ORGANIZATIONS['non_existing_external_orgs']
    }
    inverse_orgs = {props.get('Alt Name'): name for name, props in all_orgs.items() if props.get('Alt Name')}
    org_primary_names = list(all_orgs.keys())
    org_alt_names = list(inverse_orgs.keys())
    
    # First, check if the sponsor is an exact match in primary or alternate orgs
    if sponsor in org_primary_names:
        return all_orgs[sponsor]["Primary Code"]
    
    closest_valid_sponsor = find_closest_match(sponsor, org_primary_names, case_sensitive=False, threshold=85)
    if closest_valid_sponsor:
        return all_orgs[closest_valid_sponsor]["Primary Code"]
    
    if sponsor in org_alt_names:
        return all_orgs[inverse_orgs[sponsor]]["Primary Code"]
    
    closest_valid_sponsor = find_closest_match(sponsor, org_alt_names, case_sensitive=False, threshold=85)
    if closest_valid_sponsor:
        return all_orgs[inverse_orgs[closest_valid_sponsor]]["Primary Code"]
    
    # Extract titles and attempt title-based matching
    titles = extract_titles(sponsor)

    for title in titles:
        if title in org_primary_names:
            return all_orgs[title]["Primary Code"]
        
        closest_valid_sponsor = find_closest_match(title, org_primary_names, case_sensitive=False, threshold=85)
        if closest_valid_sponsor:
            return all_orgs[closest_valid_sponsor]["Primary Code"]
        
        if title in org_alt_names:
            return all_orgs[inverse_orgs[title]]["Primary Code"]
        
        closest_valid_sponsor = find_closest_match(title, org_alt_names, case_sensitive=False, threshold=85)
        if closest_valid_sponsor:
            return all_orgs[inverse_orgs[closest_valid_sponsor]]["Primary Code"]

def determine_activity_type(instance, type, on_site):
    activity_types = instance.ACTIVITY_TYPES
    if type in activity_types:
        return type

    closest_match = find_closest_match(f"{type} {'on' if on_site else 'off'} Campus", activity_types, threshold=85, case_sensitive=False)
    return closest_match

def validate_grant_discipline(instance, discipline) -> dict:
    """Validate if a discipline is in the list of valid disciplines."""

    # Retrieve list of valid disciplines
    valid_disciplines = instance.DISCIPLINES
    
    if discipline in valid_disciplines:
        return {"valid": True}
    
    # Attempt to find a close match
    closest_valid_discipline = find_closest_match(discipline, valid_disciplines, threshold=85)
    
    return {
        "valid": False,
        "suggestion": closest_valid_discipline
    }

def determine_grant_admin_unit(instance, grant):
    org_units = instance.ORG_UNITS
    org_centers = instance.ORG_CENTERS
    project_primary_dept = grant['Primary_Dept']
    
    org_unit_keys = [str(item) for item in org_units.keys()]
    if project_primary_dept in org_unit_keys:
        return project_primary_dept, org_units[project_primary_dept]['Primary Code'], None
    
    closest_valid_dept = find_closest_match(project_primary_dept, org_unit_keys, threshold=85)
    if closest_valid_dept:
        return closest_valid_dept, org_units[closest_valid_dept]['Primary Code'], None
    
    org_center_keys = [str(item) for item in org_centers.keys()]
    if project_primary_dept in org_center_keys:
        project_center = org_centers[project_primary_dept]
        return project_center['Admin Unit'], project_center['Admin Unit Code'], project_primary_dept
    
    closest_valid_center = find_closest_match(project_primary_dept, org_center_keys, threshold=85)
    if closest_valid_center:
        project_center = org_centers[closest_valid_center]
        return project_center['Admin Unit'], project_center['Admin Unit Code'], closest_valid_center
    return (None, None, None)

def proposals_sheet_append(
    self: "MigrationManager",
    grant_data,
    total_data,
    rifunds_data
    ):
    gt_manager = self.generated_template_manager
    ft_manager = self.feedback_template_manager
    next_row = gt_manager.df[SHEET_NAME].shape[0] + 1
    
    grant_id = grant_data['Grant_ID']
    grant_pln = grant_data['Project_Legacy_Number']
    
    existing_data = ft_manager.find(SHEET_NAME, {"proposalLegacyNumber": grant_id}, return_one=True) or {}
    project_sheet_entry = gt_manager.find("Project - Template", {"projectLegacyNumber": grant_pln}, return_one=True) or {}

    grant_status = grant_data['Status']
    if not grant_status:
        gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 3, 'error', "Grant is missing Status in database.")
        existing_status = existing_data.get('Status')
        if existing_status:
            grant_status = existing_status
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 3, 'notice', "Status was determined using feedback file.")
    
    
    grant_oar = project_sheet_entry.get('status')

    grant_primary_college = grant_data['Prim_College']
    if not grant_primary_college:
        gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 4, 'error', "Grant is missing Primary College in database.")
        existing_college = existing_data.get('CUNY Campus')
        if existing_college:
            grant_primary_college = existing_college
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 4, 'notice', "Primary College was determined using feedback file.")
        
    grant_instrument_type = None
    if grant_data['Instrument_Type']:
        try:
            determined_instrument_type = determine_instrument_type(self, grant_data['Instrument_Type'])
            if not determined_instrument_type:
                raise ValueError(f"Grant has invalid Instrument_Type in database: {grant_data['Instrument_Type']}")
            grant_instrument_type = determined_instrument_type
        except Exception as err:
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 5, 'error', err)
    else:
        gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 5, 'error', "Grant is missing Instrument_Type in database.")
    
    grant_sponsor = None
    if grant_data['Sponsor_1']:
        try:
            determined_sponsor = determine_sponsor(self, grant_data['Sponsor_1'])
            if not determined_sponsor:
                raise ValueError(f"Grant has invalid Sponsor_1 in database: {grant_data['Sponsor_1']}")
            grant_sponsor = determined_sponsor
        except Exception as err:
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 6, 'error', err)
    else:
        gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 6, 'warning', "Grant does not have a Sponsor_1 in database.")
    if not grant_sponsor:
        existing_sponsor = existing_data.get('Sponsor')
        if existing_sponsor:
            grant_sponsor = existing_sponsor
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 6, "notice", "Sponsor was retrieved from template file")
        elif (grant_data['Sponsor_1']):
            grant_sponsor = grant_data['Sponsor_1']
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 6, "warning", "Sponsor does not exist in external orgs sheet.")
    
    if not grant_instrument_type:
        str_id = str(grant_data['RF_Account'])
        if str_id.startswith('6'):
            grant_instrument_type = "PSC CUNY"
        elif grant_sponsor == 'CUNY':
            grant_instrument_type = 'CUNY Internal'
        else:
            existing_instrument_type = existing_data.get('Instrument Type')
            if existing_instrument_type:
                grant_instrument_type = existing_instrument_type
                gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 5, 'notice', "Instrument Type was determined using feedback file.")
        # if (grant_instrument_type and not grant_data['Instrument_Type']):
        #     self.db_manager.update_query(
        #         "grants",
        #         { "Instrument_Type": grant_instrument_type },
        #         { "Grant_ID": { "operator": "=", "value": grant_id } }
        #     )
        #     print(f"Updated Instrument Type to '{grant_instrument_type}' for grant:{grant_id}")

    grant_prime_sponsor = None
    if grant_data['Sponsor_2']:
        try:
            determined_prime_sponsor = determine_sponsor(self, grant_data['Sponsor_2'])
            if not determined_prime_sponsor:
                raise ValueError(f"Grant has invalid Sponsor_2 in database: {grant_data['Sponsor_2']}")
            grant_prime_sponsor = determined_prime_sponsor
        except Exception as err:
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 7, 'error', err)
    if not grant_prime_sponsor:
        existing_prime_sponsor = existing_data.get('Prime Sponsor')
        if existing_prime_sponsor:
            grant_prime_sponsor = existing_prime_sponsor
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 7, "notice", "Sponsor was retrieved from template file")
        elif (grant_data['Sponsor_2']):
            grant_prime_sponsor = grant_data['Sponsor_2']
            
    grant_title = project_sheet_entry.get('title')
    grant_start_date = grant_data['Start_Date'] or grant_data['Start_Date_Req']
    if not grant_start_date:
        gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 9, 'error', "Grant does not have a start date in database.")
        existing_start_date = existing_data.get('Project Start Date')
        if existing_start_date:
            grant_start_date = existing_start_date
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 9, "notice", "Start Date was retrieved from template file")
        elif (("OAR" or " oar " in grant_title) or (grant_sponsor == "JJCOAR") and grant_data['Status_Date']):
            grant_start_date = grant_data['Status_Date']
            # log
        # if (grant_start_date):
        #     self.db_manager.update_query(
        #         "grants",
        #         { "Start_Date": grant_start_date },
        #         { "Grant_ID": {
        #             "operator": "=",
        #             "value": grant_id
        #         } }
        #     )
    
    grant_end_date = grant_data['End_Date'] or grant_data['End_Date_Req']
    if not grant_end_date:
        gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 10, 'error', "Grant does not have a end date in database.")
        existing_end_date = existing_data.get('Project End Date')
        if existing_end_date:
            grant_end_date = existing_end_date
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 10, "notice", "End Date was retrieved from template file")
        elif (("OAR" or " oar " in grant_title) or (grant_sponsor == "JJCOAR") and grant_data['Status_Date']):
            grant_end_date = grant_data['Status_Date']
        # if (grant_end_date):
        #     self.db_manager.update_query(
        #         "grants",
        #         { "End_Date": grant_start_date + relativedelta(years=1) },
        #         { "Grant_ID": {
        #             "operator": "=",
        #             "value": grant_id
        #         } }
        #     )
    
    grant_activity_type = None
    if grant_data['Award_Type']:
        try:
            determined_activity_type = determine_activity_type(self, grant_data['Award_Type'], grant_data['Purpose'] != None)
            if not determined_activity_type:
                raise ValueError(f"Grant has invalid Award_Type in database: {grant_data['Award_Type']}")
            grant_activity_type = determined_activity_type
        except Exception as err:
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 11, 'error', err)
    else:
        gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 11, 'error', "Grant is missing Award_Type in database")
    if not grant_activity_type:
        if existing_data.get('Activity Type'):
            grant_activity_type = existing_data.get('Activity Type')
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 11, "notice", "Award Type was retrieved from template file")
        elif grant_instrument_type == 'PSC CUNY' or grant_instrument_type == 'CUNY Internal':
            grant_activity_type = 'Research on Campus'

    grant_discipline = None
    if grant_data['Discipline']:
        discipline_validation = validate_grant_discipline(self, grant_data['Discipline'])
        if discipline_validation['valid']:
            grant_discipline = grant_data['Discipline']
        elif discipline_validation['suggestion']:
            grant_discipline = discipline_validation['suggestion']
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 12, 'notice', f"Grant discipline value '{grant_data['Discipline']}' is not valid but a similar one was found.")
        else:
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 12, 'error', f"Grant discipline value '{grant_data['Discipline']} is not valid'")
    else:
        gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 12, 'error', "Grant does not have a discipline in database.")
        
    if not grant_discipline and grant_data['Primary_Dept']:
        alt_discipline_validation = validate_grant_discipline(self, grant_data['Primary_Dept'])
        if alt_discipline_validation['valid']:
            grant_discipline = grant_data['Primary_Dept']
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 12, 'notice', "Discipline was determined using Primary Dept.")
        elif alt_discipline_validation['suggestion']:
            grant_discipline = alt_discipline_validation['suggestion']
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 12, 'notice', "Primary Dept. assimilated a valid Discipline.")
            
    if not grant_discipline:
        existing_discipline = existing_data.get('Discipline')
        if existing_discipline:
            grant_discipline = existing_discipline
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 12, "notice", "Discipline was retrieved from template file")
    
    grant_num_budget_periods = len(total_data)
    grant_rate_cost_type = None
    if grant_data['RIndir%DC']:
        num_direct = float(grant_data['RIndir%DC'])
        if num_direct:
            grant_rate_cost_type = "Total Direct Costs (TDC)"
    if grant_data['RIndir%Per']:
        num_wages = float(grant_data['RIndir%Per'])
        if num_wages:
            grant_rate_cost_type = "Salary and Wages (SW)"
    if not grant_rate_cost_type:
        existing_rate_cost_type = existing_data.get('Indirect Rate Cost Type')
        if existing_rate_cost_type:
            grant_rate_cost_type = existing_rate_cost_type
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 15, "notice", "Rate Cost Type was retrieved from template file.")
            
    grant_idc_rate = round((float(grant_data['RIndir%DC']) if grant_rate_cost_type == "Total Direct Costs (TDC)" else (float(grant_data['RIndir%Per']) if grant_rate_cost_type == "Salary and Wages (SW)" else 0)) * 100, 1)
    
    grant_idc_cost_type_explain = grant_data['Indirect_Deviation']
    if not grant_idc_cost_type_explain:
        existing_cost_type_explain = existing_data.get('IDC Cost Type Explanation')
        if existing_cost_type_explain:
            grant_idc_cost_type_explain = existing_cost_type_explain
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 17, 'notice', "Rate Cost Type Explanation retrieved from template file.")
            
    grant_total_direct_cost = round(sum(map(lambda fund: fund['RIAmount'], rifunds_data)))
    grant_sponsor_cost = round(sum(map(lambda fund: fund['RAmount'], total_data)))
    
    grant_has_subrecipient = "Yes" if grant_data['Subrecipient_1'] else "No"
    grant_has_human_subjects = "Yes" if grant_data['Human Subjects'] else "No"
    grant_has_animal_subjects = "Yes" if grant_data['Research Animals'] else "No"
    grant_has_hazard_material = ("Yes" if grant_data['Biohazards'] else "None")
    grant_has_export_control = "Yes" if grant_data['Export Control'] else "No"
    grant_comments = grant_data['Comments']
    
    grant_has_irb_approval = ("Approved" if grant_data['IRB_Approval'] else None)
    grant_irb_approval_date = (grant_data['IRB_Start'] if grant_has_irb_approval else None)
    
    grant_idc_rate_less_on_campus_rate = "No"
    reassigned_time_yn = "No"
    reassigned_time_details = None
    
    grant_submit_date = grant_data['Date_Submitted']
    if not grant_submit_date:
        self.generated_template_manager.property_manager.append_comment(SHEET_NAME, next_row, 32, 'error', "Grant is missing Date_Submitted in the database.")
    
    grant_admin_unit_name = None
    grant_admin_unit_code = None
    grant_admin_unit_center = None
    if grant_data['Primary_Dept']:
        try:
            grant_admin_unit_name, grant_admin_unit_code, grant_admin_unit_center = determine_grant_admin_unit(self, grant_data)
            if not grant_admin_unit_name and not grant_admin_unit_code and not grant_admin_unit_center:
                raise ValueError(f"Grant has invalid Primary_Dept in database: {grant_data['Primary_Dept']}")
        except Exception as err:
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 34, 'error', err)
    else:
        gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 34, 'error', "Grant is missing Primary_Dept in database.")
            
    if not grant_admin_unit_name:
        existing_unit_name = existing_data.get('Admin Unit Name')
        if existing_unit_name:
            grant_admin_unit_name = existing_unit_name
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 34, 'notice', f"Admin Unit Name was retrieved from feedback file.")
    if not grant_admin_unit_code:
        existing_unit_code = existing_data.get('Admin Unit Code')
        if existing_unit_code:
            grant_admin_unit_code = existing_unit_code
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 35, 'notice', f"Admin Unit Code was retrieved from feedback file.")
    if grant_admin_unit_name == "Grant & Research Admin" and not grant_admin_unit_center:
        existing_unit_center = existing_data.get('John Jay Centers')
        if existing_unit_center:
            grant_admin_unit_center = existing_unit_center
            gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 33, 'notice', f"Admin Unit Code was retrieved from feedback file.")
            
    # if (not grant_start_date and grant_data['Date_Submitted'] and (grant_sponsor == "JJCOAR" or "OAR" in grant_title)):
    #     print(f"Marker: {grant_data['Status_Date']}")
    #     self.db_manager.update_query(
    #         "grants",
    #         {
    #             "Start_Date": grant_data['Status_Date']
    #         },
    #         {
    #             "Grant_ID": grant_id
    #         }
    #     )
    # if (not grant_end_date and grant_data['Status_Date'] and (grant_sponsor == "JJCOAR" or "OAR" or " oar " in grant_title)):
    #     self.db_manager.update_query(
    #         "grants",
    #         {
    #             "Start_Date": grant_data['Status_Date'] + relativedelta(years=1)
    #         },
    #         {
    #             "Grant_ID": grant_id
    #         }
    #     )
            
    
    self.generated_template_manager.append_row(
        SHEET_NAME, {
            "projectLegacyNumber": grant_pln,
            "proposalLegacyNumber": grant_id,
            "status": grant_status,
            "OAR Status": grant_oar,
            "CUNY Campus": grant_primary_college,
            "Instrument Type": grant_instrument_type,
            "Sponsor": grant_sponsor,
            "Prime Sponsor": grant_prime_sponsor,
            "Title": grant_title,
            "Project Start Date": grant_start_date,
            "Project End Date": grant_end_date,
            "Activity Type": grant_activity_type,
            "Discipline": grant_discipline,
            "Abstract": "",
            "Number of Budget Periods": grant_num_budget_periods,
            "Indirect Rate Cost Type": grant_rate_cost_type,
            "IDC Rate": grant_idc_rate,
            "IDC Cost Type Explanation": grant_idc_cost_type_explain,
            "Total Total Total Direct Cost (TDC) (TDC)s": round(grant_sponsor_cost - grant_total_direct_cost),
            "Total InTotal Total Direct Cost (TDC) (TDC)s": grant_total_direct_cost,
            "Total Sponsor Costs": grant_sponsor_cost,
            "IDC Rate Less OnCampus Rate": grant_idc_rate_less_on_campus_rate,
            "Reassigned Time YN": reassigned_time_yn,
            "Reassigned Time Details": reassigned_time_details,
            "Subrecipient": grant_has_subrecipient,
            "Human Subjects": grant_has_human_subjects,
            "IRB Protocol Status": grant_has_irb_approval,
            "IRB Approval Date": grant_irb_approval_date,
            "Animal Subjects": grant_has_animal_subjects,
            "Hazardous Materials": grant_has_hazard_material,
            "Export Control": grant_has_export_control,
            "Additional Comments": grant_comments,
            "Submission Date": grant_submit_date,
            "Admin Unit Name": grant_admin_unit_name,
            "Admin Unit Code": grant_admin_unit_code,
            "John Jay Centers": grant_admin_unit_center
        }
    )