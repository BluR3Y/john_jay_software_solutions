
SHEET_NAME = "Members - Template"

def modify_entries(self):
    # Store the sheet's content
    sheet_content = self.df[SHEET_NAME]
    # Loop through every row in the sheet
    for index, row in sheet_content.iterrows():
        # ID identifying entries in Access Database
        entry_legacy_num = row['legacyNumber']
        # Terminal progress indicator
        print(f"Current entry: {entry_legacy_num}")

        modifying_fields = []
        # Check if the 'username' needs modification (i.e., if it's NaN)
        if (isinstance(row['username'], float)):
            modifying_fields.append(('username', 'Primary_PI'))
        # Check if 'association 1' needs modification
        if (isinstance(row['association 1'], float)):
            modifying_fields.append(('association 1', 'Primary_Dept'))

        # If there are fields to modify
        if (modifying_fields):
            # If no prior logs have been created for the current sheet, initialize the property in the logger's modifications for that sheet
            if SHEET_NAME not in self.logger['modifications']:
                self.logger['modifications'][SHEET_NAME] = {
                    'Success': {},
                    'Error': {}
                }
            
            required_data = ""
            for index, field in enumerate(modifying_fields):
                required_data += field[1]
                if ((index + 1) is not len(modifying_fields)):
                    required_data += ', '
            db_data = self.execute_query("SELECT " + required_data + " FROM grants WHERE Grant_ID = ?", (entry_legacy_num,))
            if (db_data):
                username = db_data[0].get('Primary_PI')
                association = db_data[0].get('Primary_Dept')
                if (not username or not association):
                    self.logger['modifications'][SHEET_NAME]['Error'][f"{entry_legacy_num}:data"] = "Entry does not have a Primary Contact or a Primary Department"
                    next

                if (username):
                    l_name, f_name = username.split(", ")
                    sheet_content.loc[index, 'username'] = f_name + ' ' + l_name
                    self.logger['modifications'][SHEET_NAME]['Success'][f"{entry_legacy_num}:username"] = "Successfully modified username"
                if (association):
                    sheet_content.loc[index, 'association 1'] = association
                    self.logger['modifications'][SHEET_NAME]['Success'][f"{entry_legacy_num}:association"] = "Successfully modified association"
            else:
                self.logger['modifications'][SHEET_NAME]['Error'][f"{entry_legacy_num}:database"] = "Entry does not exist in Access Database"