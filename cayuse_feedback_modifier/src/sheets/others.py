from classes.Process import Process

SHEET_NAME = "Other"

def abundant_grant_record_modifier(self):
    def logic():
        # Missing Logging functionality
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

        if logger:
            self.append_logs(SHEET_NAME, logger)

    return Process(
        logic,
        "Filter and Modify Database Grant Records",
        "The process goes through the Microsoft Access database and searches for records that match the column value provided by the user. Those records will then have their value for a column, selected by the user, updated."
    )