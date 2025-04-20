import os
from bs4 import BeautifulSoup
import rapidfuzz
import re

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

def single_select_input(requestStr: str, selections: list[str]) -> str:
    if not len(selections):
        raise ValueError("Selections list can't be empty")
    elif len(selections) == 1:
        return selections[1]
    
    selection_str = ""
    for index, item in enumerate(selections):
        selection_str += f"\t{index}) - {item}\n"
    user_input = input(f"{requestStr}\n{selection_str}")

    if not user_input:
        raise Exception("Did not make a selection. Is required to continue.")
    
    if user_input.isdigit():
        numeric_selection = int(user_input)
        if numeric_selection >= len(selections):
            raise ValueError(f"{numeric_selection} is not a valid numeric selection.")
        return selections[numeric_selection]
    else:
        if user_input not in selection_str:
            raise ValueError(f"{user_input} is not a valid selection.")
        return user_input

def multi_select_input(requestStr: str, selections: list[str]) -> list[str]:
    if not len(selections):
        raise ValueError("Columns list can't be empty")
    elif len(selections) == 1:
        return selections
    
    input_str = " | ".join(selections) + f"\n{requestStr} "
    user_input = input(input_str)
    selected_properties = []

    if not user_input:
        return selected_properties
    elif user_input == "all":
        return selections
    
    for prop in user_input.split(','):
        formatted_prop = prop.strip()
        if formatted_prop not in selections:
            raise ValueError(f"The column '{formatted_prop}' does not exist in the table.")
        selected_properties.append(formatted_prop)
    return selected_properties

def find_closest_match(input, string_list, threshold=90, case_sensitive=True):
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

def request_user_confirmation(requestStr: str) -> bool:
    if not len(requestStr):
        raise ValueError("requestStr can't be empty.")
    
    user_input = input(requestStr).capitalize()
    if not user_input:
        return False
    elif user_input not in ["Yes",'Y','N',"No"]:
        raise ValueError("Invalid input for confirmation")
    
    return user_input[0] == "Y"

def reverse_dict_search(condition: dict, items: dict):
    for key, props in items.items():
        for search_key, search_prop in condition.items():
            if props.get(search_key) != search_prop:
                break
        else:
            return key