from datetime import datetime
from methods.utils import strip_html, find_closest_match
import json

SHEET_NAME = "Proposal - Template"
SHEET_COLUMNS = [
    "projectLegacyNumber",
    "proposalLegacyNumber",
    "OAR Status",
    "status",
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
    "Admin Unit NAME",
    "Admin Unit"
  ]

ORG_UNITS = None
with open('./config/john_jay_org_units.json') as f:
    ORG_UNITS = json.load(f)
ORG_CENTERS = None
with open('./config/john_jay_centers.json') as f:
    ORG_CENTERS = json.load(f)
    
DEBUG_COUNTER = 0

def determine_status(grant):
    status_threshold = datetime.strptime('2024-01-01', '%Y-%m-%d')
    project_status = grant['Status']
    project_start_date = grant['Start_Date_Req']
    project_end_date = grant['End_Date_Req']

    if project_status != "Rejected":
        if project_start_date and project_end_date:
            if project_status == "Funded":
                return ("Active" if project_end_date >= status_threshold else "Closed")
            elif project_status == "Pending":
                return ("Active" if project_start_date >= status_threshold else "Closed")
            else:
                raise Exception("Grant was assigned a status that is not valid.")
        else:
            raise Exception("Grant is missing start/end date which is required to determine the status.")
    else:
        return "Closed"
    
# *** Needs revision
def determine_instrument_type(grant):
    valid_instrument_types = ['Grant', 'Contract', 'Cooperative Agreement', 'Incoming Subaward', 'NYC/NYS MOU - Interagency Agreement', 'PSC CUNY', 'CUNY Internal']
    
    project_instrument_type = grant['Program_Type']
    if project_instrument_type:
        if project_instrument_type in valid_instrument_types:
            return project_instrument_type
        else:
            closest_match = find_closest_match(project_instrument_type, valid_instrument_types)
            if closest_match:
                return closest_match
            else:
                raise Exception(f"Grant's instrument type '{project_instrument_type}' is not a valid choice.")
    else:
        raise Exception("Grant does not have an Instrument Type")

def determine_Admin_Unit(instance, grant):
    project_primary_dept = grant['Primary_Dept']
    
    if project_primary_dept:
        if project_primary_dept in ORG_UNITS.keys():
            return project_primary_dept, ORG_UNITS[project_primary_dept]['Primary Code']
        else:
            closest_valid_dept = find_closest_match(project_primary_dept, ORG_UNITS.keys())
            if closest_valid_dept:
                return closest_valid_dept, ORG_UNITS[closest_valid_dept]['Primary Code']
            else:
                closest_valid_center = find_closest_match(project_primary_dept, ORG_CENTERS.keys())
                if closest_valid_center:
                    return ORG_CENTERS[closest_valid_center]['Admin Unit'], ORG_CENTERS[closest_valid_center]['Admin Unit Code']
                else:
                    raise Exception(f"Could not find a valid department for {project_primary_dept}")
    else:
        raise Exception("Grant does not have a primary department in the database.")

def proposals_sheet_append(self, grant):
    sheet_df = self.generated_template_manager.df[SHEET_NAME]
    next_row = sheet_df.shape[0] + 1
    
    try:
        grant_status = determine_status(grant)
    except Exception as e:
        grant_status = None
        self.generated_template_manager.comment_manager.append_comment(SHEET_NAME, next_row, 3, e)
    
    try:
        grant_admin_unit, grant_admin_unit_code = determine_Admin_Unit(self, grant)
    except Exception as e:
        grant_admin_unit = None
        grant_admin_unit_code = None
        self.generated_template_manager.comment_manager.append_comment(SHEET_NAME, next_row, 151, e)
        
    try:
        grant_instrument_type = determine_instrument_type(grant)
    except Exception as e:
        grant_instrument_type = None
        self.generated_template_manager.comment_manager.append_comment(SHEET_NAME, next_row, 7, e)

    self.generated_template_manager.append_row(SHEET_NAME, {
        "projectLegacyNumber": grant['Project_Legacy_Number'],
        "proposalLegacyNumber": grant['Grant_ID'],
        "OAR Status": grant['Status'],
        "status": grant_status,
        "CUNY Campus": grant['Prim_College'],
        "Instrument Type": grant_instrument_type,
        "Sponsor": grant['Sponsor_1'],
        "Prime Sponsor": grant['Sponsor_2'],
        "Title": grant['Project_Title'],
        "Project Start Date": grant['Start_Date_Req'],
        "Project End Date": grant['End_Date_Req'],
        "Activity Type": grant['Award_Type'],
        "Discipline": grant['Discipline'],
        "Abstract": "",
        "Admin Unit NAME": grant_admin_unit,
        "Admin Unit": grant_admin_unit_code
    })