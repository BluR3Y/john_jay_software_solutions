import os
from bs4 import BeautifulSoup
import rapidfuzz
import re

# def request_file_path(requestStr: str, validTypes: list[str]):
#     path = input(requestStr + ': ')
#     if os.path.isfile(path):
#         fileType = os.path.splitext(path)[1]
#         if fileType in validTypes:
#             return path
#         else:
#             raise Exception(f"The provided file has the extension {fileType} which is not a valid type for this request")
#     else:
#         raise Exception("The file does not exist at the provided path")
def request_file_path(requestStr: str, validTypes: list[str]):
    if not validTypes:
        raise ValueError("No file extensions were provided.")
    
    selected_path = input(requestStr)
    if not selected_path:
        raise ValueError("Failed to provide file path.")
    
    if not os.path.isfile(selected_path):
        raise FileExistsError(f"The file does not exist at the provided path: {selected_path}")
    
    file_type = os.path.splitext(selected_path)[1]
    if file_type not in validTypes:
        raise ValueError(f"The provided file has the extension {file_type} which is not a valid type for this request.")
    
    return selected_path
    
def find_closest_match(input: str, string_list: list[str], threshold:int = 80, case_sensitive: bool = True):
    if not isinstance(input, str):
        raise ValueError("The input must be a string.")
    
    if not isinstance(string_list, list) or not all(isinstance(s, str) for s in string_list):
        raise ValueError("string_list must be a list of strings.")
    
    # Use rapidfuzz.process to calculate similarity scores for all strings
    matches = rapidfuzz.process.extract(input if case_sensitive else input.lower(), string_list if case_sensitive else [item.lower() for item in string_list], scorer=rapidfuzz.fuzz.ratio, score_cutoff=threshold)
    
    if not matches:
        return None
    
    # Extract the best match
    best_match, best_score, best_index = max(matches, key=lambda x: x[1])
    return string_list[best_index]

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
    
def request_column_selection(requestStr: str, valid_columns: list[str]) -> list[str]:
    input_str = " | ".join(valid_columns) + f"\n{requestStr} "
    user_input = input(input_str)
    selected_properties = []
    
    if not user_input:
        return selected_properties
    # selected_properties = [col.strip() for col in user_input.split(',')] if user_input else []

    for prop in user_input.split(','):
        formatted_prop = prop.strip()
        if formatted_prop not in valid_columns:
            raise ValueError(f"The column '{formatted_prop}' does not exist in the table.")
        
        selected_properties.append(formatted_prop)
    return selected_properties

def find_closest_match(input, string_list, threshold=80, case_sensitive=True):
    if not isinstance(input, str):
        raise ValueError("The input must be a string.")
    
    if not isinstance(string_list, list) or not all(isinstance(s, str) for s in string_list):
        raise ValueError("string_list must be a list of strings.")
    
    formatted_items = string_list if case_sensitive else [item.lower() for item in string_list]
    formatted_input = input if case_sensitive else input.lower()

    # Use rapidfuzz.process to calculate similarity scores for all strings
    matches = rapidfuzz.process.extract(formatted_input, formatted_items, scorer=rapidfuzz.fuzz.ratio, score_cutoff=threshold)
    
    if not matches:
        for index, item in enumerate(formatted_items):
            if item.startswith(formatted_input) or item.endswith(formatted_input):
                matches = [(item, 90, index)]
                break
    if not matches:
        return None
    
    # Extract the best match
    best_match, best_score, best_index = max(matches, key=lambda x: x[1])
    return string_list[best_index]

def extract_titles(input_string):
    """
    Extracts key titles and abbreviations from a string:
    - Always includes the main title.
    - Extracts abbreviations inside parentheses.
    - Extracts titles before and after a dash (-), cleaning out the abbreviations.
    
    Parameters:
        input_string (str): The input string to extract titles from.

    Returns:
        list: A list of extracted titles, including any additional abbreviations or components.
    """
    titles = []
    
    # Always add the full title as the first entry (strip any extra whitespace)
    main_title = input_string.split('-')[0].strip()  # Capture everything before the dash
    main_title = re.sub(r"\s\([^()]*\)", "", main_title)  # Remove abbreviations inside parentheses
    if main_title:
        titles.append(main_title)
    
    # Extract abbreviations inside parentheses
    abbreviations = re.findall(r"\(([^()]+)\)", input_string)
    for abbr in abbreviations:
        abbr = abbr.strip()
        if abbr and abbr not in titles:
            titles.append(abbr)
    
    # Extract any part of the title after a dash, and clean it by removing parentheses
    after_dash = re.findall(r"(?<=\s-\s)(.*)", input_string)
    for part in after_dash:
        part = part.strip()
        cleaned_part = re.sub(r"\s\([^()]+\)", "", part)  # Remove parentheses from after-dash part
        if cleaned_part and cleaned_part not in titles:
            titles.append(cleaned_part)
    
    return titles

def get_valid_filename() -> str:
    """Ensures the user provides a valid file name."""
    while True:
        file_name = input("Enter new file name: ").strip()
        if file_name and not any(char in file_name for char in r'\/:*?"<>|'):
            return file_name
        print("Invalid file name, try again.\n")