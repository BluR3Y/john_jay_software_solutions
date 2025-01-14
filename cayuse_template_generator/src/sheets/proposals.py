from datetime import datetime

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

def determine_statuses(grant):
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

def determine_Admin_Unit(grant):
    "lol"

def determine_abstract(grant):
    return grant['Abstract']

def proposals_sheet_append(self, grant):
    sheet_df = self.generated_template_manager.df[SHEET_NAME]
    next_row = sheet_df.shape[0] + 1
    
    try:
        grant_status = determine_statuses(grant)
    except Exception as e:
        grant_status = None
        self.generated_template_manager.comment_manager.append_comment(SHEET_NAME, next_row, 3, e)
    
    try:
        grant_discipline = determine_Admin_Unit(grant)
    except Exception as e:
        grant_discipline = None
        self.generated_template_manager.comment_manager.append_comment(SHEET_NAME, next_row, 3, e)
    
    try:
        grant_abstract = determine_abstract(grant)
    except Exception as e:
        grant_abstract = None
        self.generated_template_manager.comment_manager.append_comment(SHEET_NAME, next_row, 27, e)
    
    self.generated_template_manager.append_row(SHEET_NAME, {
        "projectLegacyNumber": [grant['project_legacy_number']],
        "proposalLegacyNumber": [grant['Grant_ID']],
        "OAR Status": [grant['Status']],
        "status": grant_status,
        "CUNY Campus": [grant['Prim_College']],
        "Instrument Type": "",
        "Sponsor": [grant['Sponsor_1']],
        "Prim Sponsor": [grant['Sponsor_2']],
        "Title": [grant['Project_Title']],
        "Project Start Date": [grant['Start_Date_Req']],
        "Project End Date": [grant['End_Date_Req']],
        "Activity Type": [grant['Award_Type']],
        "Discipline": [grant['Discipline']],
        "Abstract": grant_abstract,
        "Admin Unit NAME": "",
        "Admin Unit": ""
    })