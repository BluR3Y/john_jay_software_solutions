from methods.shared_populating import determine_grant_status

SHEET_NAME = "Attachments - Template"
SHEET_COLUMNS = [
    "projectLegacyNumber",
    "form",
    "awardLegacyNumber",
    "legacyNumber",
    "modificationNumber",
    "field ",
    "attachment type",
    "filePath",
    "PI_Name",
    "RF_Account",
    "Orig_Sponsor",
    "Sponsor",
    "Status",
    "OAR Status"
  ]

def attachments_sheet_append(self, grants):
    sheet_df = self.generated_template_manager.df[SHEET_NAME]
    
    for grant_obj in grants:
        next_row = sheet_df.shape[0] + 1
        grant_data = grant_obj['grant_data']
        
        grant_id = grant_data['Grant_ID']
        grant_status = grant_data['Status']
        if grant_status != "Funded":
            continue
        
        grant_pln = grant_data['Project_Legacy_Number']
        grant_legacy_number = f"{grant_id}-award"
        
        grant_investigator = grant_data['Primary_PI']
        grant_rf_account = grant_data['RF_Account']
        grant_sponsor_1 = grant_data['Sponsor_1']
        grant_sponsor_2 = grant_data['Sponsor_2']
        grant_title = grant_data['Project_Title']
        
        grant_oar = None
        try:
                grant_oar = determine_grant_status(grant_data)
        except Exception as err:
            self.generated_template_manager.comment_manager.append_comment(
                SHEET_NAME,
                next_row,
                12,
                err
            )
        
        self.generated_template_manager.append_row(SHEET_NAME, {
            "projectLegacyNumber": grant_pln,
            "awardLegacyNumber": grant_legacy_number,
            "legacyNumber": grant_id,
            "Project Title": grant_title,
            "PI_Name": grant_investigator,
            "RF_Account": grant_rf_account,
            "Orig_Sponsor": grant_sponsor_2,
            "Sponsor": grant_sponsor_1,
            "Status": grant_status,
            "OAR Status": grant_oar,
            "Start Date": grant_data['Start_Date'] or grant_data['Start_Date_Req'],
            "End Date": grant_data['End_Date'] or grant_data['End_Date_Req']
        })