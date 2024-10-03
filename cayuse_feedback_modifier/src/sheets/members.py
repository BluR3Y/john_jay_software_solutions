SHEET_NAME = "Members - Template"

def modify_entries(self):
    # Store the sheet's content
    sheet_content = self.df[SHEET_NAME]
    # Store entries that need modifying
    modifying_entries = [[]]
    # Bundle entries to reduce number of requests made to the database
    bundle_max = 40
    # Local sheet logger
    sheet_logger = dict()
    
    # Loop through every row in the sheet
    for index, row in sheet_content.iterrows():
        if len(modifying_entries[-1]) == bundle_max:
            modifying_entries.append([])
        
        # ID identifying entries in Access Database
        entry_legacy_num = row['legacyNumber']

        modifying_fields = []
        # Check if the 'username' needs modification (i.e., if it's NaN)
        if (isinstance(row['username'], float)):
            modifying_fields.append('username')
        # Check if 'association 1' needs modification
        if (isinstance(row['association 1'], float)):
            modifying_fields.append('association')

        # If the entry has fields that need modifying
        if (modifying_fields):
            modifying_entries[-1].append({
                'index': index,
                'id': entry_legacy_num,
                'properties': modifying_fields,
            })

    # If there are entries to modify
    if (modifying_entries):

        for bundle in modifying_entries:
            bundle_ids = [item['id'] for item in bundle]
            query = f"SELECT Primary_PI, Primary_Dept, Grant_ID FROM grants WHERE Grant_ID IN ({','.join(['?' for _ in bundle_ids])})"
            db_data = self.execute_query(query, bundle_ids)
            db_data_dict = {entry["Grant_ID"]: entry for entry in db_data}

            for bundle_item in bundle:
                print(f"Current entry: {bundle_item['id']}")
                if (db_data_dict.get(bundle_item['id'])):
                    if ("username" in bundle_item['properties']):
                        username = db_data_dict[bundle_item['id']]['Primary_PI']
                        if (username):
                            l_name, f_name = username.split(", ")
                            sheet_content.loc[bundle_item['index'], 'username'] = f_name + ' ' + l_name
                        else:
                            sheet_logger[f"{bundle_item['id']}:username"] = "Entry does not have a Primary Contact"

                    if ("association" in bundle_item['properties']):
                        association = db_data_dict[bundle_item['id']]['Primary_Dept']
                        if (association):
                            sheet_content.loc[bundle_item['index'], 'association 1'] = association
                        else:
                            sheet_logger[f"{bundle_item['id']}:association"] = "Entry does not have a Primary Department" 
                else:
                    sheet_logger[f"{bundle_item['id']}:database"] = "Entry does not exist in Access Database"

        # If no prior logs have been created for the current sheet, initialize the property in the logger's modifications for that sheet
        if SHEET_NAME not in self.logger['modifications']:
            self.logger['modifications'][SHEET_NAME] = sheet_logger
        # Else, add the properties of the sheet to the class logger
        else:
            self.logger['modifications'][SHEET_NAME].update(sheet_logger)