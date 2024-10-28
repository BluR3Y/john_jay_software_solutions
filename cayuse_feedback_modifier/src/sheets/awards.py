import utils
import re
import pandas as pd

SHEET_NAME = "Award - Template"

# Method that will populate the "Discipline" column in the Microsoft Access DB
# * Requires Excel document with the project's key (Prsy) and the discipline
def populate_db_discipline(self):
    # Request path to the file from the user
    file_path = utils.request_file_path("Enter the path of the file that will be used to populate the database", ['.xlsx'])
    # Read the contents of the file
    file_content = pd.read_excel(
        file_path,
        sheet_name="prsy_index_report",
        header=4    # Specifies the row to use as the column names
    )
    sheet_logger = dict()

    project_disciplines = dict()
    # Loop through every row in the table
    for index, row in file_content.iterrows():
        primary, secondary, tertiary = re.split(r'[-\s]+', row['Prsy'])
        rf_id = primary+secondary

        if rf_id in project_disciplines and project_disciplines[rf_id]["discipline"] is not None:
            project_disciplines[rf_id]["secondary_keys"].append(tertiary)
        else:
            discipline = row.get("Discipline", None)
            # Checks if the 'Discipline' value is missing
            if not pd.isna(discipline):
                # Regex expression checks if discipline has an abbreviation
                regex_match = re.search(r'-\s*(.+)', discipline)
                # If so, the discipline is extracted from the string
                if regex_match:
                    discipline = regex_match.group(1)
            else:
                discipline = None
                sheet_logger[f"{primary}-{secondary}-{tertiary}"] = "Project is missing 'Discipline' value"

            project_disciplines[rf_id] = {
                "secondary_keys": project_disciplines.get(rf_id,{}).get("secondary_keys", []) + [tertiary],
                "discipline": discipline
            }

    current_index = 0
    num_modifications = len(project_disciplines)
    for key in project_disciplines:
        current_index += 1
        query = f"""
            UPDATE grants
            SET Discipline = ?
            WHERE RF_Account = ?;
        """
        self.execute_query(query, (project_disciplines[key]["discipline"], key))
        print(f"Database modifications are {round(current_index/num_modifications)}% complete")

        # If no prior logs have been created for the current sheet, initialize the property in the logger's modifications for that sheet
        if SHEET_NAME not in self.logger['modifications']:
            self.logger['modifications'][SHEET_NAME] = sheet_logger
        # Else, add the properties of the sheet to the class logger
        else:
            self.logger['modifications'][SHEET_NAME].update(sheet_logger)