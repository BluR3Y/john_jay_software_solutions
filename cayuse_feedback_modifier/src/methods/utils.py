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