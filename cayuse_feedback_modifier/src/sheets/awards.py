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

    discipline_query = "SELECT Name FROM LU_Discipline;"
    result = self.execute_query(discipline_query)
    project_disciplines = { discipline["Name"]: {
        "primary_keys": []
    } for discipline in result}

    # Loop through every record in the table
    for index, row in file_content.iterrows():
        primary, secondary, tertiary = re.split(r'[-\s]+', row['Prsy'])
        rf_id = primary+secondary

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
            continue

        correlating_item = None
        for key in project_disciplines:
            if key.lower() == discipline.lower():
                correlating_item = key
                break
        if (correlating_item):
            if rf_id not in project_disciplines[correlating_item]["primary_keys"]:
                project_disciplines[correlating_item]["primary_keys"].append(rf_id)
        else:
            sheet_logger[f"{primary}-{secondary}-{tertiary}"] = f"Project has the value '{discipline}' for it's Discipline field, which is an invalid value"


    for index, key in enumerate(project_disciplines):
        if project_disciplines[key]["primary_keys"]:
            primary_keys = project_disciplines[key]["primary_keys"]
            update_query = f"""
                UPDATE grants
                SET Discipline = ?
                WHERE RF_Account IN ({','.join(['?' for _ in primary_keys])})
            """
            self.execute_query(update_query, key, *primary_keys)
        print(f"Database modifications are {round(index/len(project_disciplines) * 100)}% complete")

    self.append_process_logs(SHEET_NAME, {
        "populate_db_discipline": {
        "Description": "Process processes data from an excel file which should contain a table with the RF_Account and discipline of awards",
        "logs": sheet_logger
    } })