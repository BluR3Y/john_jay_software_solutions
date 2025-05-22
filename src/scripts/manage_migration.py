import os
from tqdm import tqdm
import traceback

from packages.migration_manager import MigrationManager
from packages.workbook_manager import WorkbookManager
from modules.utils import (
    single_select_input,
    request_file_path,
    multi_select_input
)

def generate_data():
    with MigrationManager(os.getenv("ACCESS_DB_PATH"), os.getenv("EXCEL_FILE_PATH")) as migration_manager:

        # user_grant_filter = input("Migrate grants where:")
        # grant_filter = migration_manager.db_manager.parse_sql_condition(user_grant_filter)
        query_grant_ids = migration_manager.db_manager.select_query(
            table="grants",
            cols=["Grant_ID"],
            conditions={
                "End_Date_Req": {
                    "operator": ">",
                    "value": "2016-12-31"
                }
            }
        )
        grant_ids = [grant['Grant_ID'] for grant in query_grant_ids]
        for grant_id in tqdm(grant_ids, "Processing grants", unit="grant"):
            # Retrieve primary grant data
            select_grant_query = migration_manager.db_manager.select_query(
                table="grants",
                conditions={
                    "Grant_ID": {
                        "operator": "=",
                        "value": grant_id
                    }
                }
            )
            if not select_grant_query:
                migration_manager.generated_wb_manager["Errors"].append_row({
                    "Grant_ID": grant_id,
                    "Sheet": "Management",
                    "Issue": f"Could not find record for grant in table 'grants'"
                })
                continue
            else:
                select_grant_query = select_grant_query[0]

            # Retrieve "financial" records relating to grant
            select_total_query = migration_manager.db_manager.select_query(
                table="total",
                conditions={
                    "RFunds_Grant_ID": {
                        "operator": "=",
                        "value": grant_id
                    }
                }
            )
            if not select_total_query:
                migration_manager.generated_wb_manager["Errors"].append_row({
                    "Grant_ID": grant_id,
                    "Sheet": "Management",
                    "Issue": f"Could not find record for grant in table 'total'"
                })
                continue
            
            # Retrieve "RI funds" records relating to grant
            select_ri_funds_query = migration_manager.db_manager.select_query(
                table="RIfunds",
                conditions={
                    "RIFunds_Grant_ID": {
                        "operator": "=",
                        "value": grant_id
                    }
                }
            )
            if not select_ri_funds_query:
                migration_manager.generated_wb_manager["Errors"].append_row({
                    "Grant_ID": grant_id,
                    "Sheet": "Management",
                    "Issue": f"Could not find record for grant in table 'RIfunds'"
                })
                continue

            # Retrieve "costshare" records relating to grant
            select_costshare_query = migration_manager.db_manager.select_query(
                table="CostShare",
                conditions={
                    "GrantID": {
                        "operator": "=",
                        "value": grant_id
                    }
                }
            )

            # Append grant to "Proposals" sheet
            try:
                migration_manager.proposals_sheet_append(
                    select_grant_query,
                    select_total_query,
                    select_ri_funds_query,
                    select_costshare_query
                )
            except Exception as err:
                migration_manager.generated_wb_manager["Errors"].append_row({
                    "Grant_ID": grant_id,
                    "Sheet": "Proposal - Template",
                    "Issue": f"Error while adding to proposals sheet: {err}",
                    "Traceback": traceback.format_exc()
                })

            # Append grant to "Projects" sheet
            try:
                migration_manager.projects_sheet_append(select_grant_query)
            except Exception as err:
                migration_manager.generated_wb_manager["Errors"].append_row({
                    "Grant_ID": grant_id,
                    "Sheet": "Project - Template",
                    "Issue": f"Error while adding to projects sheet: {err}",
                    "Traceback": traceback.format_exc()
                })

            # Retrieve Primary Investigator records relating to grants
            select_pi_query = migration_manager.db_manager.select_query(
                table="PI_name",
                conditions={
                    "PI_Grant_ID": {
                        "operator": "=",
                        "value": grant_id
                    }
                }
            )
            if not select_pi_query:
                migration_manager.generated_wb_manager["Errors"].append_row({
                    "Grant_ID": grant_id,
                    "Sheet": "Members",
                    "Issue": f"Could not find record for grant in table 'PI_name'"
                })
                continue

            # Append grant to "Members" sheet
            try:
                migration_manager.members_sheet_append(select_grant_query, select_pi_query)
            except Exception as err:
                migration_manager.generated_wb_manager["Errors"].append_row({
                    "Grant_ID": grant_id,
                    "Sheet": "Member - Template",
                    "Issue": f"Error while adding to members sheet: {err}",
                    "Traceback": traceback.format_exc()
                })

            # Retrieve "Updates" records relating to grant
            select_dates_query = migration_manager.db_manager.select_query(
                table="Dates",
                conditions={
                    "Date_GrantID": {
                        "operator": "=",
                        "value": grant_id
                    }
                }
            )

            # Retrieve "F funds" records relating to grant
            select_ffunds_query = migration_manager.db_manager.select_query(
                table="Ffunds",
                conditions={
                    "FFunds_Grant_ID": {
                        "operator": "=",
                        "value": grant_id
                    }
                }
            )
            # Retrieve "FI funds" relating to grant
            select_fifunds_query = migration_manager.db_manager.select_query(
                table="FIFunds",
                conditions={
                    "FIFunds_Grant_ID": {
                        "operator": "=",
                        "value": grant_id
                    }
                }
            )

            # Append grants that are funded, or assigned an 'RF_Account' number to "Awards" sheet
            if select_grant_query.get('Status') == "Funded" or select_grant_query.get('RF_Account') != None:
                try:
                    migration_manager.awards_sheet_append(
                                select_grant_query,
                                select_total_query,
                                select_ri_funds_query,
                                select_dates_query,
                                select_costshare_query,
                                select_ffunds_query,
                                select_fifunds_query
                    )
                except Exception as err:
                    migration_manager.generated_wb_manager["Errors"].append_row({
                        "Grant_ID": grant_id,
                        "Sheet": "Award - Template",
                        "Issue": f"Error while adding to Award sheet: {err}",
                        "Traceback": traceback.format_exc()
                    })

def compile_changes():
    source_file_path = request_file_path("Enter the file path of the source workbook:", [".xlsx"])
    target_file_path = request_file_path("Enter the file path of the reference workbook:", [".xlsx"])
    if source_file_path == target_file_path:
        raise ValueError("Can't assign the same file to be source and reference.")

    target_wb = WorkbookManager(target_file_path).__enter__()

    with WorkbookManager(source_file_path) as source_wb:
        shared_sheets = [sheet for sheet in source_wb.get_sheet_names() if sheet in target_wb]
        if not shared_sheets:
            raise ValueError("Workbooks don't share any common sheets.")
        
        # Temp fix, until wb logging is resolved
        modified = False
        
        for sheet_name in shared_sheets:
            source_sheet_manager = source_wb[sheet_name]
            target_sheet_manager = target_wb[sheet_name]
            
            shared_columns = list(set(source_sheet_manager.df.columns) & set(target_sheet_manager.df.columns))
            record_identifiers = multi_select_input("Select columns to use as identifiers", shared_columns)

            if not record_identifiers:
                continue

            check_columns = multi_select_input("Select columns to check changes", shared_columns)
            sheet_differences = source_sheet_manager.find_differences(target_sheet_manager, record_identifiers, checking_cols=check_columns)

            if not modified and sheet_differences:
                modified = True

            print(f"Changes to {len(sheet_differences)} records determined.")
            for index, changes in sheet_differences.items():
                if changes:
                    row = source_sheet_manager[index].to_dict()
                    source_sheet_manager.update_cell(index, changes)
                    for key in changes.keys():
                        source_sheet_manager.add_issue(index, key, "notice", f"Value was changed from: {row[key]}")

        if modified and source_wb.set_write_path(request_file_path("Input file save path:", [".xlsx"])):
            source_wb._save_data()

def manage_migration():
    print(f"Current Process: {"Manage Migration"}")
    while True:
        user_selection = single_select_input("Select a Migration Manager Action:", [
            "Generate Data",
            "Compile Changes",
            "Exit Process"
        ])

        match user_selection:
            case "Generate Data":
                generate_data()
            case "Compile Changes":
                compile_changes()
            case _:
                return