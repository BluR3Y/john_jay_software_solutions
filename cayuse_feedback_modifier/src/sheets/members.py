from classes.Process import Process

SHEET_NAME = "Members - Template"

def modify_entries(self):
    def logic():
        # Store the sheet's content
        sheet_content = self.df[SHEET_NAME]
        # Store entries that need modifying
        modifying_entries = [[
           {
                "index": 0,
                "id": 9555221,
                "properties": ['username', 'association']
            }
        ]]
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
        if modifying_entries[0]:
            for bundle in modifying_entries:
                bundle_ids = [item['id'] for item in bundle]
                query = f"SELECT Primary_PI, Primary_Dept, Grant_ID FROM grants WHERE Grant_ID IN ({','.join(['?' for _ in bundle_ids])})"
                db_data = self.db_manager.execute_query(query, bundle_ids)
                db_data_dict = {entry["Grant_ID"]: entry for entry in db_data}

                for bundle_item in bundle:
                    if db_data_dict.get(bundle_item['id']):
                        if "username" in bundle_item['properties']:
                            username = db_data_dict[bundle_item['id']]['Primary_PI']
                            if username:
                                l_name, f_name = username.split(", ")
                                sheet_content.loc[bundle_item['index'], 'username'] = f_name + ' ' + l_name
                            else:
                                self.append_comment(
                                    SHEET_NAME,
                                    bundle_item['index'] + 1,
                                    sheet_content.columns.get_loc('username'),
                                    "The entry does not have a Primary Contact in the database."
                                )
                            
                        if "association" in bundle_item['properties']:
                            association = db_data_dict[bundle_item['id']]['Primary_Dept']
                            if association:
                                sheet_content.loc[bundle_item['index'], 'association 1'] = association
                            else:
                                self.append_comment(
                                    SHEET_NAME,
                                    bundle_item['index'] + 1,
                                    sheet_content.columns.get_loc('association'),
                                    "The entry does not have a Primary Department in the database."
                                )
                    else:
                        self.append_comment(
                            SHEET_NAME,
                            bundle_item['index'] + 1,
                            sheet_content.columns.get_loc('legacyNumber'),
                            f"The database does not have any record associated with the legacyNumber {bundle_item['id']}"
                        )
        if sheet_logger:
            self.append_logs(
                SHEET_NAME,
                sheet_logger
            )

    return Process(
        logic,
        'Modify Template Entries',
        "The process goes through every record in the Members sheet and validates if the values for 'username' and 'association' are populated. If those record columns are empty in the template, they will be populated with data that exists in the database"
    )