from methods.utils import find_closest_match, strip_html
from methods.shared_populating import determine_grant_status, determine_instrument_type, determine_sponsor, determine_activity_type, determine_grant_discipline, determine_grant_admin_unit

SHEET_NAME = "Award - Template"
SHEET_COLUMNS = [
    "projectLegacyNumber",
    "proposalLegacyNumber",
    "awardLegacyNumber",
    "status",
    "Status OAR",
    "modificationNumber",
    "CUNY Campus",
    "Instrument Type",
    "Sponsor",
    "Sponsor Code",
    "Sponsor Award Number",
    "Sponsor ALN",
    "Prime Sponsor",
    "Prime Sponsor Award Number",
    "Prime Sponsor ALN",
    "Title",
    "Award Notice Received",
    "Project Start Date",
    "Project End Date",
    "Award Close Date",
    "Program Name",
    "Proposal Type",
    "Activity Type",
    "John Jay Centers",
    "Admin Unit Name",
    "Admin Unit",
    "Discipline",
    "Description",
    "Abstract",
    "Proposal Key Words",
    "Award Legacy Number",
    "Account Legacy Number",
    "Legacy Modification Type",
    "Sabbatical YN",
    "Sabbatical Details",
    "Number of Budget Periods",
    "Indirect Rate Cost Type",
    "IDC Rate",
    "IDC Cost Type Explanation",
    "Total Direct Costs",
    "Total Indirect Costs",
    "Total Sponsor Costs",
    "Total Awarded Direct Costs",
    "Total Awarded Indirect Costs",
    "Total Expected Amount",
    "Obligated Direct Costs",
    "Obligated Indirect Costs",
    "Obligated Amount",
    "Anticipated Direct Costs",
    "Anticipated Indirect Costs",
    "Anticipated Amount",
    "Yr 1 Direct Costs",
    "Year 1 Indirect Costs",
    "Year 1 Total Costs",
    "Awarded Yr 1 Direct Costs",
    "Awarded Yr 1 Indirect Costs",
    "Awarded Yr 1 Total Costs",
    "Yr 2 Direct Costs",
    "Year 2 Indirect Costs",
    "Year 2 Total Costs",
    "Awarded Yr 2 Direct Costs",
    "Awarded Yr 2 Indirect Costs",
    "Awarded Yr 2 Total Costs",
    "Yr 3 Direct Costs",
    "Year 3 Indirect Costs",
    "Year 3 Total Costs",
    "Awarded Yr 3 Direct Costs",
    "Awarded Yr 3 Indirect Costs",
    "Awarded Yr 3 Total Costs",
    "Yr 4 Direct Costs",
    "Year 4 Indirect Costs",
    "Year 4 Total Costs",
    "Awarded Yr 4 Direct Costs",
    "Awarded Yr 4 Indirect Costs",
    "Awarded Yr 4 Total Costs",
    "Yr 5 Direct Costs",
    "Year 5 Indirect Costs",
    "Year 5 Total Costs",
    "Awarded Yr 5 Direct Costs",
    "Awarded Yr 5 Indirect Costs",
    "Awarded Yr 5 Total Costs",
    "Yr 6 Direct Costs",
    "Year 6 Indirect Costs",
    "Year 6 Total Costs",
    "Awarded Yr 6 Direct Costs",
    "Awarded Yr 6 Indirect Costs",
    "Awarded Yr 6 Total Costs",
    "Yr 7 Direct Costs",
    "Year 7 Indirect Costs",
    "Year 7 Total Costs",
    "Awarded Yr 7 Direct Costs",
    "Awarded Yr 7 Indirect Costs",
    "Awarded Yr 7 Total Costs",
    "Yr 8 Direct Costs",
    "Year 8 Indirect Costs",
    "Year 8 Total Costs",
    "Awarded Yr 8 Direct Costs",
    "Awarded Yr 8 Indirect Costs",
    "Awarded Yr 8 Total Costs",
    "Yr 9 Direct Costs",
    "Year 9 Indirect Costs",
    "Year 9 Total Costs",
    "Awarded Yr 9 Direct Costs",
    "Awarded Yr 9 Indirect Costs",
    "Awarded Yr 9 Total Costs",
    "Yr 10 Direct Costs",
    "Year 10 Indirect Costs",
    "Year 10 Total Costs",
    "Awarded Yr 10 Direct Costs",
    "Awarded Yr 10 Indirect Costs",
    "Awarded Yr 10 Total Costs",
    "Cost Share Required",
    "Internal Cost Share",
    "External Cost Share",
    "Total Cost Share",
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
    "Software Devpt Deliverable YN",
    "Intl Collab Partnership YN",
    "On Site",
    "On Site Location",
    "Off Site",
    "Off Site Location",
    "Subrecipient",
    "Subrecipient Names",
    "Add New Subrecipient",
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
    "Publication Restriction",
    "Foreign Talent",
    "Foreign Location",
    "Foreign Activities",
    "Potential Patent",
    "IP Third Party",
    "IP Licensed",
    "SBIR STTR",
    "Terms and Conditions",
    "Restrictions",
    "Program Income Type",
    "Reporting Milestones",
    "Terms and Conditions - Other"
  ]


# def awards_sheet_append(self, grant):
#     sheet_df = self.generated_template_manager.df[SHEET_NAME]
#     next_row = sheet_df.shape[0] + 1
  
#     try:
#         grant_instrument_type = determine_instrument_type(grant)
#     except Exception as e:
#         grant_instrument_type = None
#         self.generated_template_manager.comment_manager.append_comment(SHEET_NAME, next_row, 7, e)
    
#     self.generated_template_manager.append_row(SHEET_NAME, {
#         "projectLegacyNumber": grant['Project_Legacy_Number'],
#         "awardLegacyNumber": (str(grant['Grant_ID']) + "-award"),
#         "status": "Active",
#           "OAR Status": ""
#         "modificationNumber": 0,
#         "CUNY Campus": "",
#         "Instrument Type": "",
#         "Sponsor": "",
#           "Sponsor Code"
#         "Sponsor Award Number": "",
#         "Prime Sponsor": "",
#         "Title": "",
#         "Award Notice Recieved": "",
#         "Project Start Date": "",
#         "Project End Date": "",
#         "Program Name": "",
#         "Activity Type": "",
#         "John Jay Centers": "",
#         "Admin Unit": "",
#         "Discipline": "",
#         "Abstract": "",
#         "Award Legacy Number": "",
#         "Number of Budget Periods": "",
#         "Indirect Rate Cost Type": "",
#         "IDC Rate": "",
#         "IDC Cost Type Explanation": "",
#         "Total Awarded Direct Costs": "",
#         "Total Awarded Indirect Costs": "",
#         "Total Expected Amount": "",
#         "Yr 1 Direct Costs": "",
#         "Year 1 Indirect Costs": "",
#         "Year 1 Total Costs": "",
#         "Awarded Yr 1 Direct Costs": "",
#         "Awarded Yr 1 Indirect Costs": "",
#         "Awarded Yr 1 Total Costs": "",
#         "Total Cost Share": "",
#         "Human Subjects": "",
#         "IRB Protocol Status": "",
#         "IRB Approval Date": "",
#         "Animal Subjects": "",
#         "Hazardous Materials": "",
#         "On Site": "",
#         "Off Site": "",
#         "Subrecipient": "",
#         "Export Control": "",
#         "Award Type": ""
#     })

def awards_sheet_append(self, grants):
    for index, grant_obj in enumerate(grants, start=1):
        grant_data = grant_obj['grant_data']
        total_data = grant_obj['total_data']
        rifunds_data = grant_obj['rifunds_data']
        dates_data = grant_obj['dates_data']
        cost_share_data = grant_obj['cost_share_data']
        ffunds_data = grant_obj['ffunds_data']
        fifunds_data = grant_obj['fifunds_data']
        
        grant_pln = grant_data['Project_Legacy_Number']
        grant_id = grant_data['Grant_ID']
        existing_grant = self.feedback_template_manager.get_entry(SHEET_NAME, "awardLegacyNumber", f"{grant_id}-award")
        if existing_grant == None:
            existing_grant = {}
        
        grant_status = grant_data['Status']
        grant_oar = None
        try:
            grant_oar = determine_grant_status(grant_data)
        except Exception as err:
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                4,
                err
            )
        if not grant_oar and existing_grant:
            grant_status = existing_grant['status']
            try:
                grant_oar = determine_grant_status(**grant_data, **{
                    "Status": existing_grant['Status'],
                    "Start_Date_Req": existing_grant['Project Start Date'],
                    "End_Date_Req": existing_grant['Project End Date']
                })
            except Exception as err:
                print("Error using existing grant to determine OAR Status: ", err)
                
        grant_primary_college = grant_data['Prim_College'] or existing_grant.get("CUNY Campus")
        
        grant_instrument_type = None
        try:
            grant_instrument_type = determine_instrument_type(self, grant_data)
        except Exception as err:
            grant_instrument_type = existing_grant.get("Instrument Type")
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                7,
                err
            )
            
        grant_sponsor = None
        grant_sponsor_code = None
        try:
            grant_sponsor_code = determine_sponsor(self, grant_data['Sponsor_1'])
            grant_sponsor = grant_data['Sponsor_1']
        except Exception as err:
            grant_sponsor = existing_grant.get("Sponsor")
            grant_sponsor_code = existing_grant.get("Sponsor Code")
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                8,
                err
            )
        
        grant_prime_sponsor = None
        if grant_data['Sponsor_2']:
            try:
                grant_prime_sponsor = determine_sponsor(self, grant_data['Sponsor_2'])
            except Exception as err:
                grant_prime_sponsor = existing_grant.get('Prime Sponsor')
                self.generated_template_manager.comment_manager.append_comment(
                    SHEET_NAME,
                    index,
                    12,
                    err
                )
        
        grant_award_no = grant_data['Award_No'] or existing_grant.get('Sponsor Award Number')
        grant_title = grant_data['Project_Title'] or existing_grant.get('Title')
        award_notice_date = dates_data.get('StatusDate') or existing_grant.get('Award Notice Receive')
        project_start_date = dates_data.get('StartDate') or existing_grant.get('Project Start Date')
        project_end_date = dates_data.get('EndDate') or existing_grant.get('Project End Date')
        program_name = grant_data['Program_Type'] or existing_grant.get('Program Name')
        
        grant_activity_type = None
        try:
            grant_activity_type = determine_activity_type(grant_data)
        except Exception as err:
            grant_activity_type = existing_grant.get('Activity Type')
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                22,
                err
            )
            
        grant_discipline = None
        try:
            grant_discipline = determine_grant_discipline(self, grant_data)
        except Exception as err:
            grant_discipline = existing_grant.get('Discipline')
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                26,
                err
            )
            
        grant_abstract = (strip_html(grant_data['Abstract']) if grant_data['Abstract'] else None) or existing_grant.get('Abstract')
        
        award_legacy_no = grant_data['Award_No'] or existing_grant.get('Award Legacy Number')
        
        grant_admin_unit_name, grant_admin_unit_code, grant_admin_unit_center = (None,None,None)
        try:
            grant_admin_unit_name, grant_admin_unit_code, grant_admin_unit_center = determine_grant_admin_unit(self, grant_data)
        except Exception as err:
            grant_admin_unit_code = existing_grant.get('Admin Unit')
            grant_admin_unit_center = existing_grant.get('John Jay Centers')
            grant_admin_unit_name = existing_grant.get('Admin Unit Name')
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                index,
                25,
                err
            )
            
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
        grant_total_expected_amount = round(sum(map(lambda fund: fund['RAmount'], total_data)))
        grant_total_awarded_indirect_amount = round(sum(map(lambda fund: fund['RIAmount'], rifunds_data)))
        grant_total_awarded_direct_amount = round(grant_total_expected_amount - grant_total_awarded_indirect_amount)
        
        def safe_convert(x):
            if x == None:
                return 0
            try:
                return int(x)
            except (TypeError, ValueError):
                return 0
        
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
        
        grant_total_cost_share = round(sum(map(lambda fund: safe_convert(fund['CSBudAmount']), cost_share_data)))
        
        grant_has_subrecipient = "Yes" if grant_data['Subrecipient_1'] else "No"
        grant_has_human_subjects = "Yes" if grant_data['Human Subjects'] else "No"
        grant_has_animal_subjects = "Yes" if grant_data['Research Animals'] else "No"
        grant_has_hazard_material = ("Yes" if grant_data['Biohazards'] else "None")
        grant_has_export_control = "Yes" if grant_data['Export Control'] else "No"
        
        grant_has_irb_approval = ("Approved" if grant_data['IRB_Approval'] else None) or existing_grant.get('IRB Protocol Status')
        grant_irb_approval_date = (grant_data['IRB_Start'] if grant_has_irb_approval else None) or existing_grant.get('IRB Approval Date')
        
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