from bs4 import BeautifulSoup
import difflib
import re

# A helper function that strips HTML tags
def strip_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text()

def find_closest_match(input, list):
    closest_match = difflib.get_close_matches(input, list, n=1, cutoff=0.65)
    return closest_match[0] if closest_match else None

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