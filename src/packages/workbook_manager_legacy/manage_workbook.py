import os
from packages.log_manager import manage_logs
from packages.workbook_manager_legacy import WorkbookManager
from modules.utils import (
    single_select_input,
    multi_select_input,
    request_file_path,
    request_user_confirmation
)
    

PROCESS_NAME = "Manage Workbook"

def merge_workbooks(main_wb: WorkbookManager):
    updates_path = request_file_path("Enter the file path of the updated workbook: ", [".xlsx"])
    updates_wb = WorkbookManager(updates_path).__enter__()

    non_empty_props = lambda x: {key:val for key,val in x.items() if (val is not None and val != "")}

    selected_sheets = multi_select_input("Select which sheets to apply updates: ", list(updates_wb.df.keys()))
    include_new_rows = request_user_confirmation("Would you like to include rows that aren't already in the sheet(s): ")
    sheet_identifier = "projectLegacyNumber"
    errors = []
    for sheet in selected_sheets:
        for row_index, updated_row in enumerate(updates_wb.get_sheet(sheet, format=True, orient='records')):
            row_id = updated_row.get(sheet_identifier)
            if not row_id:
                errors.append(f"Record at index '{row_index}' in the updated file does not have a sheet_identifier")
                continue

            try:
                id_search_ref = main_wb.find(sheet, {sheet_identifier: row_id})
                if id_search_ref is None or id_search_ref.empty:
                    if include_new_rows:
                        main_wb.append_row(PROCESS_NAME, sheet, updated_row)
                    errors.append(f"Record with identifer '{row_id}' in the updated file does not exist in the main file.")
                else:
                    closest_match = main_wb.find_closest_row(updated_row, id_search_ref, 1) # Modify Threshold accordingly
                    if closest_match is None or closest_match.empty:
                        if include_new_rows:
                            main_wb.append_row(PROCESS_NAME, sheet, updated_row)
                        errors.append(f"Record at index '{row_index}' in the updated file does not closely resemble any record")
                        continue

                    match_dict = main_wb.formatDF(closest_match).to_dict()
                    changes = {
                        key: val for key, val in non_empty_props(updated_row).items()
                        if match_dict.get(key) != val
                    }
                    if changes:
                        main_wb.update_cell(PROCESS_NAME, sheet, closest_match, changes)
            except Exception as err:
                errors.append(f"Error occured while updating grant {row_id}: {err}")

    if len(errors):
        print('\n'.join(errors))

def manage_workbook():
    with WorkbookManager(os.getenv("EXCEL_FILE_PATH")) as wb:
        print(f"Current Process: {PROCESS_NAME}")
        while True:
            user_selection = single_select_input("Select a Workbook action: ", [
                "Merge Workbooks",
                "View Logs",
                "Exit Process"
            ])

            match user_selection:
                case "Merge Workbooks":
                    merge_workbooks(wb)
                case "View Logs":
                    manage_logs(wb.log_manager)
                case _:
                    return