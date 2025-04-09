from typing import TYPE_CHECKING
import os

import pathlib
from pathlib import Path

from modules.utils import find_closest_match

# Pull from: C:\Users\reyhe\OneDrive\Documents\Assistant_Role\data\Data_Pull_12_9_2024
if TYPE_CHECKING:
    # Only imported for type checking
    from packages.migration_manager import MigrationManager
    
SHEET_NAME = "Attachments - Template"

def validate_file_path(file_path):
    return os.path.exists(file_path)

def find_closest_file(base_dir, file_path):
    base_dir_obj = Path(base_dir)
    file_path_obj = Path(file_path)

    if not base_dir_obj.exists() or not base_dir_obj.is_dir():
        return None  # Base directory must exist

    relative_path = Path()  # Stores the closest matching relative path

    for part in file_path_obj.parts:

        # Get list of directories and files in the current base directory
        all_items = [f.name for f in base_dir_obj.iterdir()]
        
        closest_item = find_closest_match(part, all_items)
        if not closest_item:
            return None  # No close match found

        relative_path /= closest_item   # Build the relative closest path
        base_dir_obj /= closest_item  # Move deeper into the structure

    # return base_dir_obj if base_dir_obj.exists() else None  # Return closest match
    return relative_path  # Return only the relative closest path

def attachments_sheet_append(self: "MigrationManager", grant_data: dict):
    gt_manager = self.generated_template_manager
    ft_manager = self.feedback_template_manager
    next_row = gt_manager.df[SHEET_NAME].shape[0] + 1
    
    grant_id = grant_data['Grant_ID']
    grant_pln = grant_data['Project_Legacy_Number']
    dir_path = os.getenv("PROPOSAL_PATH")
    
    grant_attachments = ft_manager.find(
        SHEET_NAME, {
            "projectLegacyNumber": grant_pln
        },
        to_dict='records'
    )
    if grant_attachments:
        for attachment in grant_attachments:
            file_path = attachment['filePath']
            file_type = attachment['attachment type']
            attachment_form = attachment['form']
            
            if file_path:
                if not validate_file_path(os.path.join(dir_path, file_path)):
                    closest_matching_file = find_closest_file(dir_path, file_path)
                    if closest_matching_file:
                        file_path = closest_matching_file
                        gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 7, 'notice', f"Path '{file_path}' was invalid but matched a similar one.")
                    else:
                        gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 7, 'error', "Path does not point to an existing file.")
            else:
                gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 7, 'error', "Attachment does not include a file path.")
            
            gt_manager.append_row(SHEET_NAME, {
                "projectLegacyNumber": grant_pln,
                "form": attachment_form,    # Subawards -> Proposals
                "legacyNumber": str(grant_id) + ("-award" if attachment_form == "Award" else ''),
                "attachment type": file_type,
                "filePath": file_path
            })
            next_row += 1
    else:
        gt_manager.append_row(SHEET_NAME, {
            "projectLegacyNumber": grant_pln,
            "form": "Proposal",
            "legacyNumber": f"{grant_id}"
        })
        gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 0, 'error', "Grant is missing Attachments.")
        next_row += 1