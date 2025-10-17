import os
import json
import logging
import pandas as pd
from typing import Any, Literal, Union

from ..packages.workbook_manager import WorkbookManager, SheetManager
from ..modules.utils import (
    single_select_input,
    request_file_path,
    multi_select_input
)
from ..modules.column_manager import ColumnManager
from ..modules.mutation import apply_mutation

PROCESS_NAME = "Manage Workbook"

def determine_differences(base_wb: WorkbookManager):
    param_path = request_file_path("Input the file path of the workbook's search parameters: ", [".json"])
    with open(param_path) as f:
        search_params = json.load(f)

    errors = []

    with WorkbookManager(search_params["mod_path"]) as mod_wb:
        for sheet_name, sheet_props in search_params["sheets"].items():
            base_sheet = base_wb[sheet_name]
            if not base_sheet:
                errors.append(f"Sheet '{sheet_name}' does not exist in base file.")
                continue

            base_columns = list(sheet_props["columns"].keys())
            base_df = base_sheet.get_df(base_columns)

            for index, base_row in base_df.iterrows():
                record_identifiers = {}
                record_columns = {}

                # Collect identifier and comparison values from base row
                for col_key, col_props in sheet_props["columns"].items():
                    mutations = col_props.get("mutations")
                    val = base_row[col_key]
                    val = apply_mutation(val, mutations) if mutations else val

                    mod_col_key = col_props.get("mod_name", col_key)
                    if col_props.get("identifier", False):
                        record_identifiers[mod_col_key] = val
                    else:
                        record_columns[mod_col_key] = val

                # Get corresponding mod sheet and DataFrame
                mod_sheet_name = sheet_props.get("mod_name", sheet_name)
                mod_sheet = mod_wb[mod_sheet_name]
                if not mod_sheet:
                    errors.append(f"Sheet '{mod_sheet_name}' missing in mod file.")
                    continue

                mod_column_keys = list(record_identifiers.keys()) + list(record_columns.keys())
                mod_df = mod_sheet.get_df(mod_column_keys)

                # Find matching row in mod workbook using identifiers
                mod_row = find_matching_row(mod_df, record_identifiers)

                if mod_row is None:
                    errors.append(f"No matching row found in mod sheet '{mod_sheet_name}' for identifiers {record_identifiers}")
                    continue

                # Compare record columns
                for col_key, base_val in record_columns.items():
                    col_props = sheet_props["columns"][get_base_col_key(sheet_props["columns"], col_key)]
                    mod_val = mod_row[col_key]

                    mod_mutations = col_props.get("mutations")
                    mod_val = apply_mutation(mod_val, mod_mutations) if mod_mutations else mod_val

                    if base_val != mod_val:
                        logging.info(f"Difference in '{col_key}' at row {index}:\n  base: {base_val}\n  mod:  {mod_val}")

    if errors:
        logging.error("Errors encountered:\n" + '\n'.join(errors))


def find_matching_row(df: pd.DataFrame, identifiers: dict) -> Any:
    if df.empty or not identifiers:
        return None
    condition = pd.Series([True] * len(df))
    for col, val in identifiers.items():
        condition &= df[col] == val
    filtered = df[condition]
    if filtered.empty:
        return None
    return filtered.iloc[0]  # return the first match


def get_base_col_key(columns: dict, mod_col_key: str) -> str:
    """
    Given a modified column key, find the base key in the config.
    """
    for base_key, props in columns.items():
        if props.get("mod_name", base_key) == mod_col_key:
            return base_key
    return mod_col_key

# def determine_differences(base_wb: WorkbookManager):
#     param_path = request_file_path("Input the file path of the workbook's search parameters: ", [".json"])
#     search_params = json.load(open(param_path))
#     mod_wb = WorkbookManager(search_params["mod_path"]).__enter__()
#     errors = []
#     for sheet_name, sheet_props in search_params["sheets"].items():
#         base_sheet_manager: SheetManager = base_wb[sheet_name]
#         if not base_sheet_manager:
#             errors.append(f"Sheet titled '{sheet_name}' does not exist in base file.")
#             continue

#         for index, row in base_sheet_manager.get_df(list(sheet_props["columns"].keys())).iterrows():
#             record_identifiers = {}
#             record_columns = {}
#             for col_key, col_props in sheet_props["columns"].items():
#                 col_val = { f"{col_props.get('mod_name', col_key)}": apply_mutation(row[col_key], col_props["mutations"]) if col_props["mutations"] else row[col_key] }
#                 if col_props.get("identifier", False):
#                     record_identifiers.update(col_val)
#                 else:
#                     record_columns.update(col_val)
        



    
#     if len(errors):
#         logging.error('\n'.join(errors))
        


def manage_workbook():
    print(f"Current Process: {PROCESS_NAME}")
    base_wb_path = request_file_path("Input file path of managing excel file:", [".xlsx"])
    with WorkbookManager(base_wb_path) as wb:
        while True:
            user_selection = single_select_input("Select a Workbook action", [
                "Highlight Differences",
                "Exit Process"
            ])

            match user_selection:
                case "Highlight Differences":
                    determine_differences(wb)
                case _:
                    return