import re

def fill_blanks(dict1, dict2):
    for key, value in dict2.items():
        if isinstance(value, dict):
            # If value is a nested dictionary, we need to recursively call the function
            dict1[key] = fill_blanks(dict1.get(key, {}), value)
        elif key not in dict1 or dict1[key] is None:
            # If the key doesn't exist in dict1 or is None, update the value
            dict1[key] = value
    return dict1

def retrieve_pi_info(self):
    investigators = {}
    pi_fragments = {}
    people_dataframe = self.feedback_template_manager.df["Data - People"]
    people_sheet_length, people_sheet_width = people_dataframe.shape
    people_rows = people_dataframe.iloc[1:people_sheet_length - 1]
    for index, person in people_rows.iterrows():
        first_name = person[0].strip().capitalize()
        middle_name = (person[1] if isinstance(person[1], str) else "").strip().capitalize()
        last_name = person[2].strip().capitalize()
        empl_id = None
        
        enclosed_regex = r".*\(\d{8}\)$"
        if re.match(enclosed_regex, last_name):
            last_name, empl_id = last_name.split("(")
            empl_id = str(empl_id[:-1])
        else:
            empl_id = str(person[3])
        
        investigators[empl_id] = fill_blanks(investigators.get(empl_id, {}), {
                "name": {
                "first": first_name,
                "middle": middle_name,
                "last": last_name,
                "full": f"{last_name}, {first_name}"
            },
            "email": person[4]
        })
        
    association_dataframe = self.feedback_template_manager.df["Data - Associations"]
    for index, associate in association_dataframe.iterrows():
        pi_empl_id = str(associate["EMP ID"])
        if pi_empl_id:
            pi_association = associate["ASSOCIATION"]
            if pi_association:
                if pi_empl_id in investigators:
                    investigators[pi_empl_id]["association"] = pi_association
                else:
                    pi_fragments[pi_empl_id] = {
                        "email": associate["USERNAME"],
                        "association": pi_association
                    }
            else:
                raise Exception("Investigator is missing Association in 'Data - Associations' sheet")
        else:
            raise Exception("Investigator is missing Employee ID in 'Data - Associations' sheet")
        
    # Missing: Logic that fills in missing information for investigators in 'Data - Association' sheet
    # # Retrieve Primary Investigator Information
    # template_pull = self.feedback_template_manager.df["Data - Associations"][['USERNAME','ASSOCIATION']]
    # pi_info = dict()
    # for index, row in template_pull.iterrows():
    #     pi_info[row['USERNAME']] = row['ASSOCIATION']
    # pi_emails = [str(email) for email in pi_info.keys()]
    # res = self.db_manager.execute_query("SELECT PI_name FROM PI_name")
    # pi_names = set(pi['PI_name'] for pi in res)
    
    # for pi in pi_names:
    #     if pi:
    #         try:
    #             if ',' in pi:
    #                 l_name, f_name = pi.split(", ")
    #             else:
    #                 l_name, f_name = pi.rsplit(' ')
    #         except ValueError:
    #             continue
    #         closest_match = find_email_by_username(f_name, l_name, pi_emails)
    #         if closest_match:
    #             self.pi_data[f"{l_name}, {f_name}"] = {
    #                 "email": closest_match,
    #                 "association": pi_info[closest_match]
    #             }
    
    self.INVESTIGATORS = investigators