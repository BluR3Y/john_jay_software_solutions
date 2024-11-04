import os
import difflib

def request_file_path(requestStr, validTypes):
    path = input(requestStr + ': ')
    if os.path.isfile(path):
        fileType = os.path.splitext(path)[1]
        if fileType in validTypes:
            return path
        else:
            raise Exception(f"The provided file has the extension {fileType} which is not a valid type for this request")
    else:
        raise Exception("The file does not exist at the provided path")
    
def find_closest_match(input, list):
    closest_match = difflib.get_close_matches(input, list, n=1, cutoff=0.65)
    return closest_match[0] if closest_match else None

def grant_abondant_record_field_modifier(self):
    logger = list()
    while True:
        search_column = input("Input the name of the column in the grant table to filter the records: ")
        search_value = input(f"Input the value to search for in the {search_column} column: ")
        modify_column = input("Input the name of the column in the grant table that will be modified: ")
        search_result = self.execute_query(f"SELECT Grant_ID, {modify_column} FROM grants WHERE {search_column} = ?;", search_value)
        records = { item['Grant_ID']:item[modify_column] for item in search_result }

        if records:
            modify_value = input(f"Input the value that will be applied to the {modify_column} column of the records: ")
            update_query = f"""
                UPDATE grants
                SET {modify_column} = ?
                WHERE Grant_ID IN ({','.join(['?' for _ in records])})
            """
            self.execute_query(update_query, modify_value, *records)

            for id in records:
                logger.append({
                    "grant_id": id,
                    "modified_field": modify_column,
                    "previous_value": records[id],
                    "new_value": modify_value
                })
            print(f"{len(records)} records modified")
        else:
            print("No records where retrieved from the search.")

        user_decision = input("Would you like to continue with another update operation (y)es/(n)o: ")
        if not user_decision.startswith('y'):
            break

    self.append_process_logs('Database', {
        "populate_template_department": {
            "description": "Process makes modifications to the records in the 'grants' table in the Microsoft Access database.",
            "logs": logger
        }
    })