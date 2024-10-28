import pyodbc
import os

def execute_query(self, query, *args):
    connection = None
    try:
        # Open the connection
        connection = pyodbc.connect(
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        r'DBQ=' + os.getenv("ACCESS_DB_PATH") + ';'
        )
        cursor = connection.cursor()

        # Execute the query
        cursor.execute(query, *args)
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
    except pyodbc.Error as err:
        print(f"An error occured: {err}")
        # Check if a connection was established with the database
        if connection:
            # Rollback any changes made to the db if an error occured
            connection.rollback()
    finally:
        # Check if a connection was established with the database
        if connection:
            # Close the cursor
            cursor.close()
            # Always close the connection
            connection.close()