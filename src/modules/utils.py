import os
import rapidfuzz
import re

def request_file_path(requestStr: str, validTypes: list[str]):
    if not validTypes:
        raise ValueError("No file extensions were provided.")
    
    selected_path = input(requestStr)
    if not selected_path:
        raise ValueError("Failed to provide file path.")
    
    formatted_path = selected_path.strip('"')
    
    if not os.path.isfile(formatted_path):
        raise FileExistsError(f"The file does not exist at the provided path: {formatted_path}")
    
    file_type = os.path.splitext(formatted_path)[1]
    if file_type not in validTypes:
        raise ValueError(f"The provided file has the extension {file_type} which is not a valid type for this request.")
    
    return formatted_path

def single_select_input(requestMsg: str, selections: list[str], emptyMsg: str = None):
    if not requestMsg or not selections:
        raise ValueError("Missing arguments.")
    elif len(selections) == 1:
        return selections[0]
    
    input_str = ""
    for index, item in enumerate(selections):
        input_str += f"\t{index}) - {item}\n"
    input_str += f"\n{requestMsg}" + (f" or leave blank({emptyMsg}): " if emptyMsg else "")
    user_input = input(input_str)

    if not user_input:
        if emptyMsg:
            return None
        raise ValueError(f"Didn't provide selection.")
    
    if user_input.isdigit():
        numeric_selection = int(user_input)
        if numeric_selection >= len(selections):
            raise ValueError(f"{numeric_selection} is not a valid numeric selection.")
        return selections[numeric_selection]
    else:
        if user_input not in selections:
            raise ValueError(f"{user_input} is not a valid selection.")
        return user_input

def multi_select_input(requestMsg: str, selections: list[str], emptyMsg: str = None):
    if not requestMsg or not selections:
        raise ValueError("Missing arguments.")
    if len(selections) == 1:
        return selections
    
    input_str = " | ".join([*selections, "ALL"]) + f"\n{requestMsg} (comma-separated)" + (f" or leave blank({emptyMsg}): " if emptyMsg else "")
    user_input = input(input_str)

    if not user_input:
        if emptyMsg:
            return []
        raise ValueError(f"Didn't provide selections.")
    elif user_input == "ALL":
        return selections
    
    selected_properties = []
    for prop in user_input.split(','):
        formatted_prop = prop.strip()
        if formatted_prop not in selections:
            raise ValueError(f"The value '{formatted_prop}' is not a valid selection")
        selected_properties.append(formatted_prop)
    return selected_properties
    

# def find_closest_match(
#         input,
#         string_list,
#         threshold=85,
#         case_sensitive=True
#     ) -> tuple[str, int]:
#     """
#     Determines the closest similar string in a list of strings.

#     Parameters:
#         - input (str): The target string to compare against others.
#         - string_list (list[str]): A list of strings to compare against target string.
#         - threshold (int): Minimum similarity score.
#         - case_sensitive (bool): Boolean dictating whether to check case(Upper/Lower).
    
#     Returns:
#         tuple[str, int]: (best_match, best_score)
#     """
#     if not isinstance(input, str):
#         raise ValueError("The input must be a string.")
    
#     if not isinstance(string_list, list) or not all(isinstance(s, str) for s in string_list):
#         raise ValueError("string_list must be a list of strings.")
    
#     formatted_items = string_list if case_sensitive else [item.lower() for item in string_list]
#     formatted_input = input if case_sensitive else input.lower()

#     # Use rapidfuzz.process to calculate similarity scores for all strings
#     matches = rapidfuzz.process.extract(formatted_input, formatted_items, scorer=rapidfuzz.fuzz.ratio, score_cutoff=threshold)
    
#     if not matches:
#         for index, item in enumerate(formatted_items):
#             if item.startswith(formatted_input) or item.endswith(formatted_input):
#                 matches = [(item, 90, index)]
#                 break
#     if not matches:
#         return None
    
#     # Extract the best match
#     best_match, best_score, best_index = max(matches, key=lambda x: x[1])
#     return (string_list[best_index], best_score)

def find_closest_match(
        target: str,
        string_list: list[str],
        threshold: int = 85,
        case_sensitive: bool = True
) -> tuple[str, int]:
    """
    Determines the closest similar string in a list of strings.

    Parameters:
        - target (str): The string to match.
        - string_list (list[str]): List of candidate strings.
        - threshold (int): Minimum similarity score.
        - case_sensitive (bool): Whether comparison is case-sensitive.

    Returns:
        tuple[str, int]: (best_match, score) if match found, else None.
    """
    if not isinstance(target, str):
        raise ValueError("Target must be a string.")
    if not isinstance(string_list, list) or not all(isinstance(s, str) for s in string_list):
        raise ValueError("string_list must be a list of strings.")
    
    formatted_input = target if case_sensitive else target.lower()
    formatted_list = string_list if case_sensitive else [s.lower() for s in string_list]

    # Use rapidfuzz.process to calculate similarity scores for all strings
    matches = rapidfuzz.process.extract(
        formatted_input,
        formatted_list,
        scorer=rapidfuzz.fuzz.ratio,
        score_cutoff=threshold
    )

    if not matches:
        for index, item in enumerate(formatted_list):
            if item.startswith(formatted_input) or item.endswith(formatted_input):
                return (string_list[index], 90) # heuristic fallback
        return None
    
    # Extract the best match
    best_match, score, index = max(matches, key=lambda x: x[1])
    return (string_list[index], score)

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