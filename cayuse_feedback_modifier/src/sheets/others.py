from classes.Process import Process
from methods import utils

SHEET_NAME = "Other"

# ***** Must be updated to work with new DatabaseManager methods
def database_record_modifier(self):
    process_name = "Modify Database Records"
    def logic():
        
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
                
                selected_search_conditions = input(f"Input the name of the column in the '{selected_table}' table followed by the value in the selected column separated by a ':' and enclosed in double quotes, which will be used to filter records in the database. Ex: \"Discipline:Philosophy\": ")
                search_conditions = dict()
                for condition in utils.extract_quoted_strings(selected_search_conditions):
                    col, val = condition.split(':')
                    if col in table_columns:
                        search_conditions[col] = val
                    else:
                        print(f"The column '{col}' does not exist in the table '{selected_table}'.")
                        break
                
                search_query = f"""
                    SELECT {','.join(set([record_identifier, *search_conditions.keys()]))}
                    FROM {selected_table}
                    WHERE {' AND '.join([f"{col}=?" for col in search_conditions.keys()])}
                """
                search_result = self.db_manager.execute_query(search_query, *search_conditions.values())
                record_data = {item[record_identifier]:item for item in search_result}
                print(f"Search returned {len(record_data)} records.")

                if record_data:
                    selected_alter_properties = input(f"Input the name of the column in the '{selected_table}' table that will be updated followed by the new value separated by a ':' and enclosed in double quites. Ex: \"Discipline:Philosophy\": ")
                    alter_properties = dict()
                    for prop in utils.extract_quoted_strings(selected_alter_properties):
                        col, val = prop.split(':')
                        if col in table_columns:
                            alter_properties[col] = val
                        else:
                            print(f"The column '{col}' does not exist in the table '{selected_table}'")
                            break

                    missing_data_columns = alter_properties.keys() - search_conditions.keys()
                    if missing_data_columns:
                        missing_data_query = f"""
                            SELECT {','.join(set([record_identifier, *missing_data_columns]))}
                            FROM {selected_table}
                            WHERE {record_identifier} IN ({','.join(['?' for _ in record_data])})
                        """
                        missing_record_data = self.db_manager.execute_query(missing_data_query, *record_data.keys())
                        for data in missing_record_data:
                            record_data[data[record_identifier]].update(data)

                    update_query = f"""
                        UPDATE {selected_table}
                        SET {','.join([f"{prop} = ?" for prop in alter_properties.keys()])}
                        WHERE {record_identifier} IN ({','.join(['?' for _ in record_data])})
                    """
                    self.db_manager.execute_query(update_query, *alter_properties.values(), *record_data.keys())
                    self.log_manager.append_logs(SHEET_NAME, process_name, {
                        f"{selected_table}:{id}": {
                            key: f"{record_data[id][key]}:{alter_properties[key]}"
                        for key in alter_properties.keys()}
                    for id in record_data.keys()})
            else:
                print(f"Table '{selected_table}' does not exist in the database.")

            user_decision = input("Would you like to continue with another update operation (y)es/(n)o: ")
            if not user_decision.startswith('y'):
                break

    return Process(
        logic,
        process_name,
        "The database_record_modifier function provides an interactive tool for modifying records within a specified table in a connected database. It allows users to select a table, define search conditions, and update multiple records in a single operation. This function is designed for dynamic and secure interaction with the database, verifying that tables and columns exist before performing operations and using parameterized queries to avoid SQL injection risks. It encapsulates the entire process in a callable Process object, ready to be integrated into larger workflows or batch processes."
    )