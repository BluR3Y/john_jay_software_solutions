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