from bs4 import BeautifulSoup
import difflib
import rapidfuzz
import re

# A helper function that strips HTML tags
def strip_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text()

# def find_closest_match(input, list):
#     closest_match = difflib.get_close_matches(input, list, n=1, cutoff=0.85)
#     return closest_match[0] if closest_match else None

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

def find_email_by_username(first_name: str, last_name: str, email_list: list) -> str:
    # Create possible patterns to match in the email
    patterns = [
        rf"{first_name}\.{last_name}",  # Matches first.last
        rf"{first_name}{last_name}",   # Matches firstlast
        rf"{first_name[0]}{last_name}",  # Matches f_last
        rf"{first_name[0]}\.{last_name}"  # Matches f.last
    ]

    # Compile the patterns into a single regex with alternations
    combined_pattern = "|".join(patterns)

    additional_patter = rf"\.{last_name}(\d*|@)"    # matches ".lastname" with optional numbers or directly followed by an @
    possible_emails = []

    # Iterate through the email list to find a match
    for email in email_list:
        if re.search(combined_pattern, email, re.IGNORECASE):
            return email  # Return the first matched email
        elif re.search(additional_patter, email, re.IGNORECASE):
            possible_emails.append(email)
            
    # Refine possible emails to check the first name more closely
    for email in possible_emails:
        # Extract the first part of the email (before the first dot)
        first_email_part = re.split(r"[._]", email)[0].strip("0123456789")
        if first_name.lower().startswith(first_email_part.lower()):
            return email  # Return the email if the first part matches
            
    
    return None  # Return None if no match is found

def format_string(text: str) -> str:
    # Remove leading and trailing spaces
    text = text.strip()
    
    # Remove unnecessary data enclosed in parentheses
    text = re.sub(r'\(.*?\)', '', text)
    
    # Remove extra spaces left after removing parentheses
    return text.strip()

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