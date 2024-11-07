from classes.Process import Process

SHEET_NAME = "Other"

def database_record_modifier(self):
    def logic():
        # Missing logging functionality
        logger = list()
        
        # Retrieve all tables in the database
        tables = []
        for row in self.db_manager.cursor.tables():
            if row.table_type == "TABLE":
                tables.append(row.table_name)

        while True:
            selected_table = input("Enter the name of the table whose records you wish to alter: ")
            if selected_table in tables:
                self.db_manager.execute_query(f"SELECT TOP 1 * FROM {selected_table}")
                table_columns = [column[0] for column in self.db_manager.cursor.description]
                record_identifier = table_columns[0]
                
                selected_search_column = input(f"Input the name of the column in the '{selected_table}' table which will be used to filter records in the database: ")
                if selected_search_column in table_columns:
                    selected_search_value = input(f"Input the value to search for in the '{selected_search_column}' column: ")
                    search_result = self.db_manager.execute_query(f"SELECT {record_identifier} FROM {selected_table} WHERE {selected_search_column} = ?;", selected_search_value)
                    records = [item[record_identifier] for item in search_result]

                    if records:
                        print(f"Search returned {len(records)} records.\n")
                        selected_modify_column = input(f"Input the name of the column in the '{selected_table}' table whose value will be updated: ")
                        if selected_modify_column in table_columns:
                            selected_modify_value = input(f"Input the new value that will be applied to the '{selected_modify_column}' column of the record(s): ")
                            update_query = f"""
                                UPDATE {selected_table}
                                SET {selected_modify_column} = ?
                                WHERE {record_identifier} IN ({','.join(['?' for _ in records])})
                            """
                            self.db_manager.execute_query(update_query, selected_modify_value, *records)
                            print(f"The following records from the table '{selected_table}' were modified: {records}")
                        else:
                            print(f"The column '{selected_modify_column}' does not exist in the table.")
                    else:
                        print("Search returned 0 records.")
                else:
                    print(f"The column '{selected_search_column}' does not exist in the table '{selected_table}'.")
            else:
                print(f"Table '{selected_table}' does not exist in the database.")

            user_decision = input("Would you like to continue with another update operation (y)es/(n)o: ")
            if not user_decision.startswith('y'):
                break

    return Process(
        logic,
        "Modify Database Records",
        "The process "
    )