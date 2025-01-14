
SHEET_NAME = "Members - Template"
SHEET_COLUMNS = [
    "projectLegacyNumber",
    "form",
    "legacyNumber",
    "modificationNumber",
    "username",
    "role",
    "association 1 (name)",
    "association 1",
    "credit 1",
    "association 2",
    "credit 2",
    "association 3",
    "credit 3",
    "association 4",
    "credit 4"
  ]

def determine_username(grant):
    pass

def members_sheet_append(self, grant):
    sheet_df = self.generated_template_manager.df[SHEET_NAME]
    next_row = sheet_df.shape[0] + 1
    
    try:
        grant_username = determine_username(grant)
    except Exception as e:
        grant_username = None
        self.generated_template_manager.comment_manager.append_comment(SHEET_NAME, next_row, 4, e)
    
    self.generated_template_manager.append_row(SHEET_NAME, {
        "projectLegacyNumber": [grant['project_legacy_number']],
        "form": "proposal",
        "legacyNumber": [grant['Grant_ID']],
        "username": grant_username
    })