import os

from ..modules.utils import(
    single_select_input,
    request_file_path
)
from ..modules.record_manager import RecordManager
from ..packages.workbook_manager import WorkbookManager
# from packages.content_manager import ContentManager
from ..modules.content_manager import ContentManager

def compile_attachments():
    with RecordManager(os.getenv("ATTACHMENT_RECORD_PATH")) as attachment_manager:
        source_path = request_file_path("Enter the path of the workbook with attachments", [".xlsx"])
        source_wb = WorkbookManager(source_path).__enter__()

        attachments_sheet_manager = source_wb["Attachments - Template"]
        sheet_columns = attachments_sheet_manager.df.columns
        required_cols = ["projectLegacyNumber", "form", "attachment type", "filePath", "legacyNumber"]
        if not all(iter(req_col in sheet_columns for req_col in required_cols)):
            raise ValueError("Not all required columns are present in the attachments sheet.")

        counter = 0
        for attachment in attachments_sheet_manager.get_df(format=True).to_dict(orient='records'):
            grant_pln = attachment.get('projectLegacyNumber')
            form_type = attachment.get('form')
            attachment_type = attachment.get('attachment type')
            attachment_path = attachment.get('filePath')
            grant_legacy_number = attachment.get('legacyNumber')
            if not attachment_manager.find_record({
                "project_legacy_number": grant_pln,
                "form_type": form_type,
                "attachment_path": attachment_path
            }):
                attachment_manager.add_record({
                    "project_legacy_number": grant_pln,
                    "form_type": form_type,
                    "attachment_type": attachment_type,
                    "attachment_path": attachment_path,
                    "legacy_number": grant_legacy_number
                })
                counter += 1
        print(f"Finished append {counter} attachments.")

def populate_attachments():
    with RecordManager(os.getenv("ATTACHMENT_RECORD_PATH")) as attachment_manager:
        with WorkbookManager(os.getenv("EXCEL_FILE_PATH")) as wb_manager:
            proposal_sheet_manager = wb_manager["Proposal - Template"]
            attachments_sheet_manager = wb_manager["Attachments - Template"]

            grants = proposal_sheet_manager.df[["proposalLegacyNumber", "projectLegacyNumber", "OAR Status", "Instrument Type"]]

            for grant in grants.to_dict(orient='records'):
                grant_pln = grant.get("projectLegacyNumber")
                grant_id = grant.get("proposalLegacyNumber")
                grant_oar = grant.get("OAR Status")
                grant_instrument_type = grant.get('Instrument Type')
                is_awarded = grant_oar == "Funded"
                is_psc = grant_instrument_type == "PSC CUNY"

                if is_awarded and not is_psc:
                    grant_attachments = attachment_manager.find_record({
                        "project_legacy_number": grant_pln,
                        "legacy_number": grant_id
                    })
                    if not grant_attachments:
                        attachments_sheet_manager.append_row({
                            "projectLegacyNumber": grant_pln,
                            "legacyNumber": grant_id
                        })
                        attachments_sheet_manager.add_issue(
                            attachments_sheet_manager.df.shape[0] - 1,
                            "projectLegacyNumber",
                            "error",
                            "Grant is missing attachments"
                        )
                        continue

                    for attachment in grant_attachments:
                        attachments_sheet_manager.append_row({
                            "projectLegacyNumber": grant_pln,
                            "form": attachment.get('form_type'),
                            "awardLegacyNumber": f"{grant_id}-award" if attachment.get('form_type') == "Award" else "",
                            "legacyNumber": grant_id,
                            "attachment type": attachment.get('attachment_type'),
                            "filePath": attachment.get('attachment_path')
                        })
                    
                # grant_attachments = attachment_manager.find_record({
                #     "project_legacy_number": grant_pln,
                #     "legacy_number": grant_id
                # })
                # if not grant_attachments:
                #     attachments_sheet_manager.append_row({
                #         "projectLegacyNumber": grant_pln,
                #         "legacyNumber": grant_id
                #     })
                #     attachments_sheet_manager.add_issue(
                #         attachments_sheet_manager.df.shape[0] - 1,
                #         "projectLegacyNumber",
                #         "error",
                #         "Grant is missing attachments"
                #     )
                #     continue

                # award_attachments = []
                # proposal_attachments = []
                # for attachment in grant_attachments:
                #     if attachment.get('form_type') == "Award":
                #         award_attachments.append(attachment)
                #     else:
                #         proposal_attachments.append(attachment)
                
                # for attachment in proposal_attachments:
                #     attachments_sheet_manager.append_row({
                #         "projectLegacyNumber": grant_pln,
                #         "form": "Proposal",
                #         "legacyNumber": grant_id,
                #         "attachment type": attachment.get('attachment_type'),
                #         "filePath": attachment.get('attachment_path')
                #     })

                # if is_awarded:
                #     if not award_attachments:
                #         attachments_sheet_manager.append_row({
                #             "projectLegacyNumber": grant_pln,
                #             "form": "Award",
                #             "legacyNumber": grant_id,
                #         })
                #         attachments_sheet_manager.add_issue(
                #             attachments_sheet_manager.df.shape[0] - 1,
                #             "projectLegacyNumber",
                #             "error",
                #             "Grant is missing 'Award' attachments"
                #         )
                #         continue

                #     for attachment in award_attachments:
                #         attachments_sheet_manager.append_row({
                #             "projectLegacyNumber": grant_pln,
                #             "form": "Award",
                #             "legacyNumber": grant_id,
                #             "attachment type": attachment.get('attachment_type'),
                #             "filePath": attachment.get('attachment_path')
                #         })
                
            wb_manager.set_write_path(request_file_path("Save file at:", [".xlsx"]))
            wb_manager._save_data()

# def copy_attachments():
#     with ContentManager(os.getenv("ATTACHMENT_STORAGE_PATH"), os.path.join(os.getenv("SAVE_PATH"), "attachment_files")) as content_manager:
#         with WorkbookManager(os.getenv("EXCEL_FILE_PATH")) as wb_manager:
#             attachment_sheet_manager = wb_manager["Attachment - Template"]

#             for index, attachment in attachment_sheet_manager.get_df(["filePath"], format=True).iterrows():
#                 file_path = attachment.get('filePath')
#                 if file_path and file_path not in content_manager.paths:
#                     if not content_manager.relative_file_exists(file_path):
#                         closest_file = content_manager.find_closest_file(file_path)
#                         if not closest_file:
#                             attachment_sheet_manager.add_issue(index, "filePath", "error", "File does not exist in folder")
#                             continue

#                         content_manager.add_file(closest_file)
#                         attachment_sheet_manager.add_issue(index, "filePath", "warning", f"File does not exist in folder but is similar to: {closest_file}")
#                     else:
#                         content_manager.add_file(file_path)
            
#             wb_manager.set_write_path("C:/Users/reyhe/OneDrive/Documents/JJay/test_environment/test_attachment_copy_results.xlsx")
#             wb_manager._save_data()
def copy_attachments():
    with ContentManager(os.getenv('ATTACHMENT_STORAGE_PATH'), os.path.join(os.getenv("SAVE_PATH"), "attachment_files")) as content_manager:
        with WorkbookManager(os.getenv("EXCEL_FILE_PATH")) as wb_manager:
            attachment_sheet_manager = wb_manager["Attachments - Template"]

            for index, attachment in attachment_sheet_manager.get_df(["filePath"], format=True).iterrows():
                try:
                    file_path = attachment.get('filePath')
                    # if not file_path or content_manager.relative_dest_file_exists(file_path):
                    #     continue
                    if not file_path:
                        continue
                    if content_manager.relative_dest_file_exists(file_path):
                        attachment_sheet_manager.add_issue(index, "filePath", "notice", "Path exists for different attachment.")

                    if not content_manager.relative_source_file_exists(file_path):
                        closest_file = content_manager.find_closest_relative_file(file_path)
                        if not closest_file:
                            raise ValueError("File does not exist in source folder")
                        
                        content_manager.copy_file(closest_file)
                        attachment_sheet_manager.add_issue(index, "filePath", "warning", f"File does not exist in folder but is similar to: {closest_file}")
                    else:
                        content_manager.copy_file(file_path)
                except Exception as err:
                    attachment_sheet_manager.add_issue(index, "filePath", "error", err)
            wb_manager.set_write_path(request_file_path("Save file path", [".xlsx"]))
            wb_manager._save_data()

def manage_attachments():
    print("Current Process: Attachment Manager")
    while True:
        user_selection = single_select_input("Select an Attachment Manager Action", [
            "Compile Attachments",
            "Populate Attachments",
            "Copy Attachments",
            "Exit Process"
        ])

        match user_selection:
            case "Compile Attachments":
                compile_attachments()
            case "Populate Attachments":
                populate_attachments()
            case "Copy Attachments":
                copy_attachments()
            case _:
                return