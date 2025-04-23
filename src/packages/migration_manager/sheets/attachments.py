from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from packages.migration_manager import MigrationManager

SHEET_NAME = "Attachments - Template"

def attachments_sheet_append(self: "MigrationManager", grant_data: dict):
    file_manager = self.attachment_manager
    gt_manager = self.generated_template_manager
    ft_manager = self.feedback_template_manager
    next_row = gt_manager.df[SHEET_NAME].shape[0] + 1

    grant_id = grant_data['Grant_ID']
    grant_pln = grant_data['Project_Legacy_Number']

    grant_attachments = ft_manager.find(
        SHEET_NAME, {
            "projectLegacyNumber": grant_pln
        },
        to_dict='records'
    )
    if not grant_attachments:
        gt_manager.append_row(
            self.process_name,
            SHEET_NAME, {
            "projectLegacyNumber": grant_pln,
            "form": "Proposal",
            "legacyNumber": f"{grant_id}"
        })
        gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 0, 'error', "Grant is missing Attachments.")
        next_row += 1
        return
    
    for attachment in grant_attachments:
        file_path = attachment['filePath']
        file_type = attachment['attachment type']
        attachment_form = attachment['form']

        if file_path:
            try:
                file_manager.add_file(file_path)
            except (FileExistsError, ValueError, IsADirectoryError) as err:
                if isinstance(err, FileExistsError):
                    closest_matching_file = file_manager.find_closest_file(file_path)
                    if closest_matching_file:
                        file_path = closest_matching_file
                        gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 7, 'notice', f"Path '{file_path}' was invalid but matched a similar one.")
                    else:
                        gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 7, 'error', "Path does not point to an existing file.")
                elif isinstance(err, IsADirectoryError):
                    gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 7, 'error', "Path does not point to a file.")
                else:
                    gt_manager.property_manager.append_comment(SHEET_NAME, next_row, 7, 'notice', err)
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