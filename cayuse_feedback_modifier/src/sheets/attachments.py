import os

SHEET_NAME = "Attachments - Template"

def verify_entries(self):
    # Store the sheet's content
    sheet_content = self.df[SHEET_NAME]
    sheet_logger = dict()
    
    # Loop through every row in the sheet
    for index, row in sheet_content.iterrows():

        # Store the path of the file that will be verified
        attachment_path = row['filePath']
        
        if not os.path.isfile(attachment_path):
            sheet_logger[f"{row['legacyNumber']}:filePath"] = "File does not exist"



    # If no prior logs have been created for the current sheet, initialize the property in the logger's modifications for that sheet
    if SHEET_NAME not in self.logger['modifications']:
        self.logger['modifications'][SHEET_NAME] = sheet_logger
    # Else, add the properties of the sheet to the class logger
    else:
        self.logger['modifications'][SHEET_NAME].update(sheet_logger)