from datetime import datetime
from methods.utils import strip_html, find_closest_match, format_string, extract_titles
from methods.shared_populating import determine_grant_status, determine_grant_discipline, determine_grant_admin_unit
import json

SHEET_NAME = "Proposal - Template"
SHEET_COLUMNS = [
    "projectLegacyNumber",
    "proposalLegacyNumber",
    "status",
    "OAR Status",
    "S2S reference id",
    "CUNY Campus",
    "Sponsor Deadline",
    "Instrument Type",
    "Sponsor",
    "Prime Sponsor",
    "Program Officer Contact Info",
    "Sponsor App No",
    "Sponsor Guidelines Options",
    "Sponsor Guidelines Explanation",
    "Sponsor Guidelines URL",
    "Sponsor Guidelines Attachment",
    "Submission Limit",
    "Title",
    "Project Start Date",
    "Project End Date",
    "Proposal Type",
    "Activity Type",
    "Prelim Prop Req YN",
    "Discipline",
    "Submission Method",
    "Other Submission Method",
    "Description",
    "Abstract",
    "Sabbatical YN",
    "Sabbatical Details",
    "Number of Budget Periods",
    "Indirect Rate Cost Type",
    "IDC Rate",
    "IDC Cost Type Explanation",
    "Total Total Total Direct Cost (TDC) (TDC)s",
    "Total InTotal Total Direct Cost (TDC) (TDC)s",
    "Total Sponsor Costs",
    "Year 1 Total Direct Cost (TDC)s",
    "Year 1 InTotal Direct Cost (TDC)s",
    "Year 1 Total Costs",
    "Year 2 Total Direct Cost (TDC)s",
    "Year 2 InTotal Direct Cost (TDC)s",
    "Year 2 Total Costs",
    "Year 3 Total Direct Cost (TDC)s",
    "Year 3 InTotal Direct Cost (TDC)s",
    "Year 3 Total Costs",
    "Year 4 Total Direct Cost (TDC)s",
    "Year 4 InTotal Direct Cost (TDC)s",
    "Year 4 Total Costs",
    "Year 5 Total Direct Cost (TDC)s",
    "Year 5 InTotal Direct Cost (TDC)s",
    "Year 5 Total Costs",
    "Year 6 Total Direct Cost (TDC)s",
    "Year 6 InTotal Direct Cost (TDC)s",
    "Year 6 Total Costs",
    "Year 7 Total Direct Cost (TDC)s",
    "Year 7 InTotal Direct Cost (TDC)s",
    "Year 7 Total Costs",
    "Year 8 Total Direct Cost (TDC)s",
    "Year 8 InTotal Direct Cost (TDC)s",
    "Year 8 Total Costs",
    "Year 9 Total Direct Cost (TDC)s",
    "Year 9 InTotal Direct Cost (TDC)s",
    "Year 9 Total Costs",
    "Year 10 Total Direct Cost (TDC)s",
    "Year 10 InTotal Direct Cost (TDC)s",
    "Year 10 Total Costs",
    "IDC Rate Less OnCampus Rate",
    "IDC Rate Documentation",
    "Detailed Budget Proposal",
    "Budget Justification",
    "Cost Share Required",
    "Mandatory Cost Share YN",
    "Voluntary Cost Share YN",
    "Voluntary CS Amount",
    "Voluntary CS Justification",
    "Internal Cost Share",
    "External Cost Share",
    "Total Cost Share",
    "Reassigned Time YN",
    "Reassigned Time Details",
    "App to Other Agencies YN",
    "Space Changes Reno or Addtl YN",
    "Additional Space Explanation",
    "Specialized IT YN",
    "Purpose Not Research YN",
    "College Equipment Used YN",
    "Equipment List",
    "Library Resources YN",
    "Library Resources List",
    "Library Resources Costs",
    "On Site",
    "On Site Location",
    "Off Site",
    "Off Site Location",
    "Subrecipient",
    "Subrecipient Names",
    "Subrecipient Attachment",
    "Subrecipient Admin Contact",
    "Subrecipient PI Contact",
    "Human Subjects",
    "Clinical Trial YN",
    "HE Application",
    "IRB Protocol Status",
    "HE Studies",
    "IRB Approval Date",
    "HE Reason",
    "Animal Subjects",
    "Animal Subjects Types",
    "AE Application",
    "Animal Subj Protocol Status",
    "AE Application Numbers",
    "IACUC Approval Date",
    "Animal Studies at College YN",
    "Animal Studies Off Site",
    "Animal Subjects Euthanized YN",
    "Euthanasia Consistent AVMA YN",
    "AE Species Involved",
    "AE Application Reason",
    "Hazardous Materials",
    "DURC YN",
    "Propriety Info Protection YN",
    "NDA YN",
    "NDA Attachment",
    "Software Devpt Deliverable YN",
    "Intl Collab Partnership YN",
    "Protocol Number",
    "Protocol Type",
    "Study Type",
    "Requires Registration",
    "Multi Site Study",
    "Study Phase",
    "Export Control",
    "EC Items",
    "EC Country",
    "International Travel",
    "International Travel Country",
    "EC Info Tech",
    "Encryption",
    "Publication Restriction YN",
    "Foreign Talent",
    "Foreign Location",
    "Foreign Activities",
    "Potential Patent",
    "IP Third Party",
    "IP Licensed",
    "SBIR STTR",
    "Supporting Documents",
    "Additional Comments",
    "Submission Date",
    "John Jay Centers",
    "Admin Unit Name",
    "Admin Unit Code"
  ]
    
ACTIVITY_ASSOCIATIONS = {
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

def determine_instrument_type(self, grant):
    valid_types = self.INSTRUMENT_TYPES
    project_award_type = grant['Award Type']

    if project_award_type:
        type_letter, type_title = project_award_type.split('-')
        type_letter.strip()
        type_title.strip()

        for type_name, association in valid_types.items():
            if type_letter in association.keys():
                return type_name
            closest_valid_type = find_closest_match(type_title, [str(item) for item in association.values()], case_sensitive=False)
            if closest_valid_type:
                return type_name

    str_id = str(grant['Grant_ID'])
    if str_id.startswith('6'):
        return "PSC CUNY"
        

def determine_sponsor(instance, sponsor):
    if not sponsor:
        raise Exception("Grant does not have a sponsor assigned to it in the database.")
    
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
    
    closest_valid_sponsor = find_closest_match(sponsor, org_primary_names, case_sensitive=False)
    if closest_valid_sponsor:
        return all_orgs[closest_valid_sponsor]["Primary Code"]
    
    if sponsor in org_alt_names:
        return all_orgs[inverse_orgs[sponsor]]["Primary Code"]
    
    closest_valid_sponsor = find_closest_match(sponsor, org_alt_names, case_sensitive=False)
    if closest_valid_sponsor:
        return all_orgs[inverse_orgs[closest_valid_sponsor]]["Primary Code"]
    
    # Extract titles and attempt title-based matching
    titles = extract_titles(sponsor)

    for title in titles:
        if title in org_primary_names:
            return all_orgs[title]["Primary Code"]
        
        closest_valid_sponsor = find_closest_match(title, org_primary_names, case_sensitive=False)
        if closest_valid_sponsor:
            return all_orgs[closest_valid_sponsor]["Primary Code"]
        
        if title in org_alt_names:
            return all_orgs[inverse_orgs[title]]["Primary Code"]
        
        closest_valid_sponsor = find_closest_match(title, org_alt_names, case_sensitive=False)
        if closest_valid_sponsor:
            return all_orgs[inverse_orgs[closest_valid_sponsor]]["Primary Code"]

    raise Exception(f"Failed to determine a sponsor code for '{sponsor}'")

def determine_activity_type(grant):
    award_type = grant['Award_Type']
    if award_type and award_type in ACTIVITY_ASSOCIATIONS:
        return ACTIVITY_ASSOCIATIONS[award_type]

def proposals_sheet_append(self, grants):
    for index, grant_obj in enumerate(grants, start=1):
        grant_data = grant_obj['grant_data']
        total_data = grant_obj['total_data']
        rifunds_data = grant_obj['rifunds_data']
        
        grant_id = grant_data['Grant_ID']
        existing_grant = {}
        if grant_id:
            retrieved_entry = self.feedback_template_manager.get_entry(SHEET_NAME, "proposalLegacyNumber", existing_grant)
            if retrieved_entry != None:
                existing_grant = retrieved_entry
        else:
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                1,
                "Grant is missing Grant_ID in the database"
            )
        
        grant_pln = grant_data['Project_Legacy_Number']
        if not grant_pln:
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                0,
                "Grant is missing Project_Legacy_Number in the database"
            )

        grant_status = None
        grant_oar = None
        try:
            grant_oar = determine_grant_status(grant_data)
            grant_status = grant_data['Status']
        except Exception as e:
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                2,
                e
            )
        if not grant_status and existing_grant.get('Status'):
            try:
                grant_oar = determine_grant_status(**grant_data, **{
                    "Status": existing_grant['Status'],
                    "Start_Date_Req": existing_grant['Project Start Date'],
                    "End_Date_Req": existing_grant['Project End Date']
                })
                grant_status = existing_grant['Status']
            except Exception as e:
                print("Error using existing entry to determine Status: ", e)
        
        grant_primary_college = grant_data['Prim_College'] or existing_grant.get("CUNY Campus")
        if not grant_primary_college:
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                5,
                "Grant is missing Prim_College in the database."
            )
            
        grant_instrument_type = None
        try:
            grant_instrument_type = determine_instrument_type(self, grant_data)
        except Exception as e:
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                7,
                e
            )
            
        grant_sponsor = None
        try:
            grant_sponsor = determine_sponsor(self, grant_data['Sponsor_1'])
        except Exception as e:
            # print(e)
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                8,
                e
            )
            
        grant_prime_sponsor = None
        if grant_data['Sponsor_2']:
            try:
                grant_prime_sponsor = determine_sponsor(self, grant_data['Sponsor_2'])
            except Exception as e:
                self.generated_template_manager.comment_manager.append_comment(
                    SHEET_NAME,
                    index,
                    9,
                    e
                )
            
        grant_title = grant_data['Project_Title'] or existing_grant.get('Title')
        if not grant_title:
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                17,
                "Grant is missing Project_Title in database"
            )
            
        grant_start_date = grant_data['Start_Date_Req'] or grant_data['Start_Date'] or existing_grant.get('Project Start Date')
        if not grant_start_date:
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                18,
                "Grant is missing Start_Date in database"
            )
            
        grant_end_date = grant_data['End_Date_Req'] or grant_data['End_Date'] or existing_grant.get('Project End Date')
        if not grant_end_date:
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                19,
                "Grant is missing End_Date in database"
            )
        
        grant_activity_type = None
        try:
            grant_activity_type = determine_activity_type(grant_data)
        except Exception as e:
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                20,
                e
            )
        
        grant_discipline = None
        try:
            grant_discipline = determine_grant_discipline(self, grant_data)
        except Exception as e:
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                23,
                e
            )
        if not grant_discipline and existing_grant.get('Discipline'):
            try:
                grant_discipline = determine_grant_discipline(self, {
                    **grant_data,
                    **{
                        "Discipline": existing_grant['Discipline']
                    }
                })
            except Exception as e:
                print("Error occured while attempting to use existing grant data to determine a Discipline")
        
        grant_abstract = strip_html(grant_data['Abstract']) if grant_data['Abstract'] else None
        
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
        
        grant_idc_rate = round((float(grant_data['RIndir%DC']) if grant_rate_cost_type == "Total Direct Costs (TDC)" else (float(grant_data['RIndir%Per']) if grant_rate_cost_type == "Salary and Wages (SW)" else 0)) * 100, 1)
        grant_idc_cost_type_explain = grant_data['Indirect_Deviation']
        grant_total_direct_cost = round(sum(map(lambda fund: fund['RIAmount'], rifunds_data)))
        grant_sponsor_cost = round(sum(map(lambda fund: fund['RAmount'], total_data)))
        print(grant_id, grant_num_budget_periods, grant_rate_cost_type, grant_idc_rate, grant_idc_cost_type_explain, grant_total_direct_cost, grant_sponsor_cost)
        
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
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                149,
                "Grant is missing Date_Submitted in the database"
            )
            
        grant_admin_unit_name, grant_admin_unit_code, grant_admin_unit_center = (None,None,None)
        try:
            grant_admin_unit_name, grant_admin_unit_code, grant_admin_unit_center = determine_grant_admin_unit(self, grant_data)
        except Exception as e:
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                151,
                e
            )

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