import os
import json
import logging
from packages.workbook_manager_beta import WorkbookManager, SheetManager
# from content.proposal_data_set import proposal_data_set_config
from modules.utils import (
    single_select_input,
    request_file_path,
    multi_select_input
)
from modules.column_manager import ColumnManager

PROCESS_NAME = "Manage Workbook"

# def determine_differences(base_wb: WorkbookManager):
#     modified_path = proposal_data_set_config["file_path"]
#     with WorkbookManager(modified_path, "C:/Users/reyhe/OneDrive/Desktop/highlighted_modified_v2.xlsx") as modified_wb:
#         errors = []
#         for sheet_name, sheet_config in proposal_data_set_config["sheets"].items():
#             modified_sheet_manager: SheetManager = modified_wb[sheet_name]
#             if not modified_sheet_manager:
#                 errors.append(f"Modified file does not contain the sheet '{sheet_name}'")
#                 continue

#             sheet_identifier: ColumnManager = sheet_config["sheet_identifier"]
#             for row_idx, row_content in modified_sheet_manager.df.iterrows():
#                 row_content_dict = SheetManager.format_df(row_content).to_dict()
#                 record_id = row_content_dict[sheet_identifier["name"]]
#                 if record_id is None:
#                     errors.append(f"Record on line '{row_idx}' modified sheet is missing its identifier")
#                     modified_sheet_manager.add_issue(row_idx, modified_sheet_manager.df.columns.get_loc(sheet_identifier["name"]), 'error', "Missing identifier")
#                     continue
#                 for checking_prop in sheet_config["properties"]:
#                     base_sheet_manager = base_wb.get_sheet(checking_prop["sheet"])

#                     base_column_name = checking_prop.get_alias()
#                     if base_column_name not in base_sheet_manager.df.columns:
#                         errors.append(f"The column '{base_column_name}' does not exist in the sheet '{checking_prop["sheet"]}'")
#                         break

#                     base_record_ref = base_sheet_manager.find({sheet_identifier.get_alias(): record_id}, return_one=True)
#                     if base_record_ref is None:
#                         errors.append(f"Record with identifer: '{record_id}' does not exist in base file.")
#                         continue
                    
#                     base_record = base_record_ref.to_dict()
#                     if base_record[base_column_name] != row_content_dict[checking_prop["name"]]:
#                         modified_sheet_manager.add_issue(row_idx, modified_sheet_manager.df.columns.get_loc(checking_prop["name"]), 'warning', f"Cell was modified. Previous value was '{base_record[base_column_name]}'")
        
#         if len(errors):
#             logging.error('\n'.join(errors))

def determine_differences(ref_wb: WorkbookManager):
    base_path = request_file_path("Input file path of the base workbook's search parameters: ", [".json"])
    base_parameters = json.load(open(base_path))
    with WorkbookManager(base_parameters["file_path"], "C:/Users/reyhe/OneDrive/Desktop/highlighted_modified_v2.xlsx") as base_wb:
        errors = []

        # for sheet in base_parameters["sheets"]:
        for sheet_name, sheet_config in base_parameters["sheets"].items():
            base_sheet_manager: SheetManager = base_wb[sheet_name]
            if not base_sheet_manager:
                errors.append(f"Base file does not contain the sheet titled: {sheet_name}")
                continue
            
            sheet_columns: list = sheet_config["columns"]
            identifier_index = next(iter(col_index for col_index, col_config in enumerate(sheet_columns) if col_config["name"] == sheet_config["record_identifier"]))
            if identifier_index == None:
                errors.append(f"Configuration for sheet '{sheet_name}' is missing record identifier.")
                continue
            
            record_identifier = ColumnManager(sheet_columns.pop(identifier_index))
            for row_idx, row_ref in base_sheet_manager.df.iterrows():
                row_content = SheetManager.format_df(row_ref).to_dict()
                record_id = row_content[record_identifier["name"]]
                

        logging.warning('\n'.join(errors))
            
# Last Here

def manage_workbook():
    with WorkbookManager(os.getenv("EXCEL_FILE_PATH")) as wb:
        print(f"Current Process: {PROCESS_NAME}")
        while True:
            user_selection = single_select_input("Select a Workbook action: ", [
                "Highlight Differences",
                "Exit Process"
            ])

            match user_selection:
                case "Highlight Differences":
                    determine_differences(wb)
                case _:
                    return