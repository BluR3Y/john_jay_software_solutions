import pyodbc
import os
import re
import datetime
from typing import Union

from . import DatabaseLogManager

class DatabaseManager:
    # Define valid operators and keywords
    OPERATORS = [
        '=', '<>', '!=', '<', '<=', '>', '>=',
        'LIKE', 'NOT LIKE', 'REGEXP', 'NOT REGEXP',
        'IN', 'NOT IN', 'IS', 'IS NOT', 'BETWEEN'
    ]
    LOGICAL_OPERATORS = ['AND', 'OR']
    NULL_VALUES = ['NULL', 'Null']
    
    def __init__(self, db_path: str):
        if not db_path:
            raise ValueError("A database file path was not provided to the DatabaseManager.")
        if not os.path.exists(db_path):
            raise ValueError(f"No database exists at the path: {db_path}")
        
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        log_file_dir = os.path.dirname(db_path)
        self.log_manager = DatabaseLogManager(os.path.join(log_file_dir, "database_logs.json"))
        
    # Only envoked when using "with"(context manager)
    def __enter__(self):
        """Initialize the database connection when entering the context."""
        self.init_db_connection()
        return self
    
    # Only envoked when using "with"(context manager)
    def __exit__(self, exc_type, exc_value, traceback):
        """Close the database connection when exiting the context."""
        self.terminate_db_connection()
        
    def init_db_connection(self):
        """Initialize the database connection."""
        try:
            # Open the connection
            self.connection = pyodbc.connect(
                r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
                r'DBQ=' + self.db_path + ';'
            )
            self.cursor = self.connection.cursor()
        except pyodbc.Error as err:
            raise ConnectionError(f"An error occured while connecting to database: {err}")
        
    def terminate_db_connection(self):
        """Terminate the database connection."""
        if self.connection:
            try:
                self.cursor.close()
                self.connection.close()
            except pyodbc.Error as err:
                raise ConnectionError(f"An error occured while closing the database: {err}")
        # Save logger changes
        self.log_manager.save_logs()
        
    def get_db_tables(self):
        tables = []
        for row in self.cursor.tables():
            if row.table_type == "TABLE":
                tables.append(row.table_name)
        return tables

    def get_table_columns(self, table):
        """Retrieve table columns."""
        try:
            query = f"SELECT * FROM {table} WHERE 1=0"
            self.cursor.execute(query)
            columns = [column[0] for column in self.cursor.description]
            return columns
        except pyodbc.Error as err:
            print(f"An error occurred while querying the database: {err}")
            if self.connection:
                self.connection.rollback()
    
    def select_query(self, table: str, cols: list[Union[str, tuple]], conditions: dict = None, all: bool = True) -> list[dict]:
        """Execute a 'SELECT' query to the database."""
        db_tables = self.get_db_tables()
        if table not in db_tables:
            raise ValueError(f"The table '{table}' does not exist in the database.")

        formatted_cols = ', '.join([(f"{col[0]} AS {col[1]}" if isinstance(col, tuple) else col) for col in cols])
        query = f"SELECT {formatted_cols} FROM {table}"
        values = []
        
        if conditions:
            cond_str, cond_vals = self.destruct_query_conditions(conditions)
            query += f" WHERE {cond_str}"
            values = cond_vals
            
        # Execute query
        self.cursor.execute(query, values)
        
        if all:
            rows = self.cursor.fetchall()
            return [dict(zip([column[0] for column in self.cursor.description], row)) for row in rows] if rows else []
        
        row = self.cursor.fetchone()
        return dict(zip([column[0] for column in self.cursor.description], row)) if row else None
    
    def update_query(self, process: str, table: str, cols: dict[str, Union[None, str, int, bool, datetime.date]], conditions: dict = None):
        "Execute an update query."
        try:
            if table not in self.get_db_tables():
                raise ValueError(f"The table '{table}' does not exist in the database.")
            if not cols:
                raise ValueError("No columns provided for update.")
            
            table_columns = self.get_table_columns(table)
            table_row_identifier = table_columns[0]
            affecting_rows = self.select_query(table, [table_row_identifier, *cols.keys()], conditions)
            
            if not affecting_rows:
                raise ValueError("Could not find records that satisfied given parameters.")
            
            for row in affecting_rows:
                changing_fields = {key:{"prev_value": row[key], "new_value": val} for key, val in cols.items() if (key in row and row[key] != val)}
                if not changing_fields:
                    continue
                
                formatted_cols = ', '.join([f"{col} = ?" for col in changing_fields.keys()])
                query_str = f"UPDATE {table} SET {formatted_cols} WHERE {table_row_identifier} = ?"
                query_vals = [values['new_value'] for values in changing_fields.values()]

                self.cursor.execute(query_str, [*query_vals, row[table_row_identifier]])
                
                self.log_manager.append_runtime_log(process, changing_fields)
            
            self.connection.commit()
        except ValueError as err:
            print(f"ValueError: {err}")
            if self.connection:
                self.connection.rollback()
            
    def destruct_query_conditions(self, conditions: dict) -> tuple[str, list]:
        """Destructure the Columns and Values of an SQL query.
        
        Returns:
            A tuple containing:
            - The parameterized SQL condition string.
            - The list of values to be used as parameters.
        """
        query_values = []

        def format_condition(cond) -> str:
            # If condition is a dict, process it accordingly.
            if isinstance(cond, dict):
                # Handle logical operators (AND/OR)
                for operator in ['AND', 'OR']:
                    if operator in cond:
                        sub_conditions = cond[operator]
                        # Allow for more than two conditions
                        formatted_conditions = f" {operator} ".join(format_condition(sub) for sub in sub_conditions)
                        return f"({formatted_conditions})"

                # Handle comparison operators and other conditions
                for column, details in cond.items():
                    operator = details['operator']
                    value = details['value']

                    if operator in ['IN', 'NOT IN']:
                        # Assume value is iterable and not a single string
                        query_values.extend(value)
                        placeholders = ', '.join('?' for _ in value)
                        return f"{column} {operator} ({placeholders})"

                    elif operator == 'BETWEEN':
                        # Expecting value to be a pair: (start, end)
                        query_values.extend([value[0], value[1]])
                        return f"{column} {operator} ? AND ?"

                    elif operator in ['LIKE', 'NOT LIKE', 'REGEXP', 'NOT REGEXP']:
                        query_values.append(value)
                        return f"{column} {operator} ?"

                    elif operator in ['IS', 'IS NOT']:
                        # Assuming value is a constant like NULL
                        return f"{column} {operator} {value}"

                    else:
                        # Default: Comparison operators (e.g. =, <>, !=, <, <=, etc.)
                        query_values.append(value)
                        return f"{column} {operator} ?"
            
            # Fallback: convert condition to string
            return str(cond)

        formatted_query = format_condition(conditions)
        return formatted_query, query_values
        # Example:
        # {
        #     "AND": [
        #         {"Grant_ID": {"operator": ">", "value": 30}},
        #         {"RF_Account": {"operator": "IS NOT", "value": "NULL"}},
        #         {
        #             "OR": [
        #                 {"Primary_PI": {"operator": "LIKE", "value": "%Smith%"}},
        #                 {"Primary_Dept": {"operator": "=", "value": "Psychology"}}
        #             ]
        #         },
        #         {"Discipline": {"operator": "IN", "value": ["Sociology","Political Science","Psychology"]}}
        #     ]
        # }

    def parse_query_conditions(self, condition_str: str, valid_columns: list = None) -> dict:
        """
        Parse a SQL condition string into a nested query object.
        
        Args:
            condition_str (str): The SQL condition string.
            valid_columns (list): A list of allowed column names. If provided,
                                the function will raise an error for unknown columns.
        
        Returns:
            dict: A nested dictionary representing the query conditions.
        """

        def cast_value(val: str):
            """
            Convert a string value to an appropriate Python type.
            - Remove surrounding quotes (single or double).
            - Convert to int or float if possible.
            - Leave as string otherwise.
            """
            val = val.strip()
            # Remove surrounding quotes if present
            if (val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"')):
                val = val[1:-1]
                return val  # Return as string (quotes removed)

            # Attempt to convert to int or float
            try:
                if '.' in val:
                    return float(val)
                return int(val)
            except ValueError:
                # Return original string if numeric conversion fails
                return val

        def is_valid_operator(operator: str) -> bool:
            return operator in self.OPERATORS

        def split_condition(condition: str):
            """
            Try to split the condition into a left part, an operator, and a right part.
            We sort operators by length (longest first) so that multiword operators are matched first.
            """
            for operator in sorted(self.OPERATORS, key=len, reverse=True):
                # Use word boundaries for alphabetic operators and plain escape for symbols.
                if operator.replace(' ', '').isalpha():
                    pattern = r'\b' + re.escape(operator) + r'\b'
                else:
                    pattern = re.escape(operator)
                if re.search(pattern, condition, re.IGNORECASE):
                    parts = re.split(pattern, condition, maxsplit=1, flags=re.IGNORECASE)
                    if len(parts) == 2:
                        return parts[0].strip(), operator.upper(), parts[1].strip()
            return None, None, None

        def split_by_logical_operator(condition: str, logical_operator: str):
            """
            Splits the condition string by a logical operator, but only at the top level
            (i.e. not within any parentheses).
            """
            parts = []
            bracket_level = 0
            current_tokens = []
            tokens = condition.split()
            for token in tokens:
                bracket_level += token.count('(')
                bracket_level -= token.count(')')
                if bracket_level == 0 and token.upper() == logical_operator:
                    parts.append(" ".join(current_tokens))
                    current_tokens = []
                else:
                    current_tokens.append(token)
            if current_tokens:
                parts.append(" ".join(current_tokens))
            if len(parts) > 1:
                return parts
            return None

        def parse_sub_condition(sub_condition: str):
            sub_condition = sub_condition.strip()

            # Remove outer parentheses if they enclose the entire condition.
            if sub_condition.startswith('(') and sub_condition.endswith(')'):
                balance = 0
                for i, char in enumerate(sub_condition):
                    if char == '(':
                        balance += 1
                    elif char == ')':
                        balance -= 1
                    if balance == 0 and i < len(sub_condition) - 1:
                        break
                else:
                    # They enclose the whole condition.
                    sub_condition = sub_condition[1:-1].strip()

            # Look for logical operators at the top level.
            for logical_operator in self.LOGICAL_OPERATORS:
                parts = split_by_logical_operator(sub_condition, logical_operator)
                if parts is not None:
                    return {logical_operator: [parse_sub_condition(part) for part in parts]}

            # At this point, assume the condition is a single expression.
            left, operator, right = split_condition(sub_condition)
            if left and operator and right:
                left = left.strip()
                right = right.strip()

                if valid_columns is not None and left not in valid_columns:
                    raise ValueError(f"Invalid column: {left}")

                # Handle NULL checks: if right contains one of the NULL keywords, assume it's a NULL check.
                if any(null_val.upper() == right.upper() for null_val in self.NULL_VALUES):
                    # Cast to None for Python if desired, or leave as 'NULL'
                    return {left: {'operator': operator, 'value': 'NULL'}}

                # Handle IN/NOT IN clauses.
                if operator in ['IN', 'NOT IN']:
                    if right.startswith('(') and right.endswith(')'):
                        # Remove the surrounding parentheses and split on commas.
                        values = [cast_value(v) for v in right[1:-1].split(',')]
                        return {left: {'operator': operator, 'value': values}}

                # Handle BETWEEN clause.
                if operator == 'BETWEEN':
                    parts = re.split(r'\bAND\b', right, flags=re.IGNORECASE)
                    if len(parts) == 2:
                        lower, upper = parts[0].strip(), parts[1].strip()
                        return {left: {'operator': operator, 'value': (cast_value(lower), cast_value(upper))}}

                # Handle LIKE, NOT LIKE, REGEXP, NOT REGEXP and others.
                return {left: {'operator': operator, 'value': cast_value(right)}}

            raise ValueError(f"Unable to parse condition: {sub_condition}")

        return parse_sub_condition(condition_str)