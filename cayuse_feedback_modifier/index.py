import pandas as pd
import pyodbc
import os
import json

# Load the Excel file
filepath = r'C:\Users\reyhe\OneDrive\Documents\Assistant_Role\data\Cayuse_Feedback_Modifications_7_25_2024\Legacy Data Template John Jay College - Cayuse Review 07.15.24.xlsx'
sheet = 'Members - Template'
df = pd.read_excel(filepath, sheet_name=sheet)
logger = {
    'filename': os.path.basename(filepath),
    'sheet': sheet,
    'changes': {}
}

def execute_query(query, parameters):
    connection = None
    # Define the path to Access database
    db_path = r'C:\Users\reyhe\OneDrive\Documents\Assistant_Role\data\New_RF_Grant_Status-Working_DB_rev2-3-23v2_Backup.accdb'

    try:
        # Open the connection
        connection = pyodbc.connect(
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        r'DBQ=' + db_path + ';'
        )
        cursor = connection.cursor()

        # Execute the query
        cursor.execute(query, parameters)
        # If the query modifies the database, make sure to commit
        if query.lower().strip().startswith(('insert', 'update', 'delete')):
            connection.commit()
        # Optionally fetch results if needed
        if query.lower().strip().startswith('select'):
            columns = [column[0] for column in cursor.description]
            # Fetch the rows
            rows = cursor.fetchall()

            data = []
            for row in rows:
                row_dict = {columns[i]: row[i] for i in range(len(columns))}
                data.append(row_dict)
            return data

    except pyodbc.Error as e:
        print(f"An error occured: {e}")
        if connection:
            connection.rollback()   # Rollback any changes if error occurs
    finally:
        if connection:
            # Close the cursor
            cursor.close()
            # Always close the connection
            connection.close()

def modify_username(index, username, logger):
    if (username):
        l_name, f_name = username.split(", ")
        df.loc[index, 'username'] = f_name + ' ' + l_name
        logger['Success'].append('Username')
    else:
        logger['Error']['Username'] = "Entry does not have a Primary Contact"        

def modify_association(index, association, logger):
    if (association):
        df.loc[index, 'association 1'] = association
        logger['Success'].append('Association 1')
    else:
        logger['Error']['Primary Department'] = "Entry does not have a Primary Department"

def modify_entries():
    # Loop throgh every row in the excel document
    for index, row in df.iterrows():
        # ID identifying entries in Access Database
        entry_legacy_num = row['legacyNumber']
        print(f"Current entry: {entry_legacy_num}")
        modifying_fields = []

        if (isinstance(row['username'], float)):
            modifying_fields.append(('username', 'Primary_PI'))
        if (isinstance(row['association 1'], float)):
            modifying_fields.append(('association 1', 'Primary_Dept'))
        

        if (modifying_fields):
            entry_logger = {
                'Success': [],
                'Error': {}
            }
            required_data = ""
            for index, field in enumerate(modifying_fields):
                required_data += field[1]
                if ((index + 1) is not len(modifying_fields)):
                    required_data += ', '
            db_data = execute_query("SELECT " + required_data + " FROM grants WHERE Grant_ID = ?", (entry_legacy_num,))
            if (db_data):
                if (db_data[0].get('Primary_PI')):
                    modify_username(index, db_data[0]['Primary_PI'], entry_logger)
                if (db_data[0].get('Primary_Dept')):
                    modify_association(index, db_data[0]['Primary_Dept'], entry_logger)
            else:
                entry_logger['Error']['Database'] = "Entry does not exist in Access Database"

            logger['changes'][entry_legacy_num] = entry_logger
            

# Save changes to excel file
# Optional argument: index=False
def save_excel_changes(filepath, as_copy = False):
    file_dir = os.path.dirname(filepath)
    file_name = os.path.basename(filepath)
    if (as_copy):
        filepath = f"{file_dir}\\{os.path.splitext(file_name)[0]} - modified_copy.xlsx"
    df.to_excel(filepath, sheet_name=sheet, index=True)

    with open(file_dir + '/excel_modifier_logger.json', 'w') as json_file:
        json.dump(logger, json_file)

modify_entries()
save_excel_changes(filepath, True)