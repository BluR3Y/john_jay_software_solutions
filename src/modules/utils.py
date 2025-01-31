import os
from bs4 import BeautifulSoup
import rapidfuzz
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
    
def find_closest_match(input, string_list, threshold=80, case_sensitive=True):
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