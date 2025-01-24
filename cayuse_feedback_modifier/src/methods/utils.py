import os
import difflib
import re

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

# Caution: Deprecated
def extract_quoted_strings(input_str):
    """
    Extracts all strings enclosed in double quotes from the input string.
    
    Args:
        input_str (str): The input string containing quoted segments.
        
    Returns:
        list of str: A list of strings that were enclosed in double quotes.
    """
    conditions = []
    inside_quotes = False
    current_condition = ""

    for char in input_str:
        if char == '"' and not inside_quotes:
            inside_quotes = True
            current_condition = ""  # Start a new quoted string
        elif char == '"' and inside_quotes:
            inside_quotes = False
            conditions.append(current_condition)  # End the quoted string
        elif inside_quotes:
            current_condition += char  # Add characters inside quotes

    if inside_quotes:
        raise ValueError("Input contains an unmatched quote.")

    return conditions

def request_user_selection(requestStr: str, validSelections: list[str]) -> str:
    selection_str = ""
    for index, selection in enumerate(validSelections):
        selection_str += f"\t{index}) - {selection}\n"
    user_input = input(f"{requestStr}\n{selection_str}")
    if user_input:
        if user_input.isdigit():
            numeric_selection = int(user_input)
            if numeric_selection < len(validSelections):
                return validSelections[numeric_selection]
            else:
                raise Exception(f"{numeric_selection} is not a valid numeric selection.")
        else:
            if user_input in validSelections:
                return user_input
            else:
                raise Exception(f"{user_input} is not a valid selection.")
    else:
        raise Exception("Did not make a selection. Is required to continue.")

def parse_query_conditions(condition_str, valid_columns):
    """
    Parses a plain WHERE condition string into a structured Python dictionary and validates column names.

    Args:
        condition_str (str): The plain WHERE condition string (e.g., "age > 30 AND department = 'Sales'").
        valid_columns (list): A list of valid column names to validate against.

    Returns:
        dict: A dictionary representing the parsed conditions.

    Raises:
        ValueError: If a column in the condition is not valid.
    """
    # Define a list of logical operators
    logical_operators = ["AND", "OR"]

    # Function to split conditions based on logical operators
    def split_conditions(condition):
        pattern = r'\b(AND|OR)\b'
        parts = re.split(pattern, condition, flags=re.IGNORECASE)
        return [p.strip() for p in parts if p.strip()]

    # Recursive function to parse conditions
    def parse_recursive(conditions):
        result = {}
        i = 0

        while i < len(conditions):
            part = conditions[i]

            if part.upper() in logical_operators:
                logical_op = part.upper()
                left = result
                right = parse_recursive(conditions[i + 1:])
                return {logical_op: [left, right]}

            # Match the column, operator, and value using regex
            match = re.match(r"(\w+)\s*(=|<>|!=|<|<=|>|>=|LIKE|NOT LIKE|IN|NOT IN|BETWEEN|IS NULL|IS NOT NULL|REGEXP|NOT REGEXP)\s*(.+)?", part, re.IGNORECASE)
            if match:
                column, operator, value = match.groups()

                # Check if the column is valid
                if column not in valid_columns:
                    raise ValueError(f"Invalid column name: {column}")

                # Handle value in IN or BETWEEN (could be a range or a list)
                if operator in ["IN", "NOT IN", "BETWEEN"]:
                    value = value.strip()
                    # Handle ranges in BETWEEN (e.g., BETWEEN 1 AND 10)
                    if operator == "BETWEEN":
                        value = value.split("AND")
                        value = [v.strip() for v in value]

                    # Handle IN as a list (e.g., IN (1, 2, 3))
                    elif operator in ["IN", "NOT IN"]:
                        value = value.strip("()").split(",")
                        value = [v.strip() for v in value]
                
                result[column] = {"operator": operator, "value": value.strip() if isinstance(value, str) else value}
                i += 1
            else:
                i += 1

        return result

    # Split conditions and parse recursively
    conditions = split_conditions(condition_str)
    return parse_recursive(conditions)

# Example:
# {
#     "AND": [
#         {"age": {"operator": "IN", "value": ["25", "30", "35"]}},
# #         {"department": {"operator": "IN", "value": ["'Sales'", "'Marketing'"]}}
#         {
#             "OR": [
#                 {"department": {"operator": "=", "value": "'Sales'"}},
#                 {"salary": {"operator": ">=", "value": 50000}}
#             ]
#         },
#         {"name": {"operator": "LIKE", "value": "'J%'"}},
#         {"status": {"operator": "IS NOT NULL", "value": ""}}
#     ]
# }