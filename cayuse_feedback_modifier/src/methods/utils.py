import os
import difflib
import re

def request_file_path(requestStr: str, validTypes: list[str]):
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

# Define valid operators and keywords
OPERATORS = ['=', '<>', '!=', '<', '<=', '>', '>=', 'LIKE', 'NOT LIKE', 'REGEXP', 'NOT REGEXP', 'IN', 'NOT IN', 'IS', 'IS NOT', 'BETWEEN']
LOGICAL_OPERATORS = ['AND', 'OR']
NULL_VALUES = ['NULL', 'Null']
PARENTHESIS = r"\((.*?)\)"

def parse_query_conditions(condition_str, valid_columns):
    # Helper function to check if an operator is valid
    def is_valid_operator(operator):
        return operator in OPERATORS

    # Helper function to split condition into left and right parts
    def split_condition(condition):
        for operator in OPERATORS:
            if operator in condition:
                left, right = condition.split(operator, 1)
                if is_valid_operator(operator):  # Only proceed if the operator is valid
                    return left.strip(), operator, right.strip()
        return None, None, None

    # Function to parse the condition recursively
    def parse_sub_condition(sub_condition):
        # If condition is grouped in parentheses, extract and recurse
        if sub_condition.startswith('(') and sub_condition.endswith(')'):
            sub_condition = sub_condition[1:-1]
            return parse_query_conditions(sub_condition, valid_columns)

        # Look for logical operators AND/OR
        for logical_operator in LOGICAL_OPERATORS:
            parts = sub_condition.split(logical_operator, 1)
            if len(parts) > 1:
                left = parse_sub_condition(parts[0].strip())
                right = parse_sub_condition(parts[1].strip())
                return {logical_operator: [left, right]}

        # Split based on operators and handle each operator type
        left, operator, right = split_condition(sub_condition)
        if left and operator and right:
            left = left.strip()
            right = right.strip()

            # Check for NULL condition
            if any(null_val in right for null_val in NULL_VALUES):
                return {left: {'operator': 'IS', 'value': right}}

            # Handle IN, NOT IN
            if operator in ['IN', 'NOT IN']:
                values = right[1:-1].split(',')
                return {left: {'operator': operator, 'value': [v.strip() for v in values]}}

            # Handle LIKE, NOT LIKE, REGEXP, NOT REGEXP
            if operator in ['LIKE', 'NOT LIKE', 'REGEXP', 'NOT REGEXP']:
                return {left: {'operator': operator, 'value': right}}

            # Handle BETWEEN
            if operator == 'BETWEEN':
                lower, upper = right.split('AND')
                return {left: {'operator': operator, 'value': (lower.strip(), upper.strip())}}

            # Otherwise return normal condition
            return {left: {'operator': operator, 'value': right}}

        return {}

    # Main function logic
    condition_str = condition_str.strip()

    # Start parsing
    return parse_sub_condition(condition_str)

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