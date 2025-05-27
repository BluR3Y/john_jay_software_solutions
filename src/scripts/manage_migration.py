import os
from tqdm import tqdm
import traceback

from packages.migration_manager import MigrationManager
from packages.workbook_manager import WorkbookManager
from modules.utils import (
    single_select_input,
    request_file_path,
    multi_select_input,
    request_user_confirmation
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

            if select_grant_query.get('Discipline') and select_grant_query.get('Discipline').isdigit():
                select_grant_query["Discipline"] = migration_manager.LU_DISCIPLINES.get(int(select_grant_query.get('Discipline')))

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
                continue

            # Append grant to "Projects" sheet
            try:
                migration_manager.projects_sheet_append(select_grant_query)
            except Exception as err:
                print(err)
                migration_manager.generated_wb_manager["Errors"].append_row({
                    "Grant_ID": grant_id,
                    "Sheet": "Project - Template",
                    "Issue": f"Error while adding to projects sheet: {err}",
                    "Traceback": traceback.format_exc()
                })
                continue

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
                                select_dates_query,
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

# def generate_attachments():

#     with WorkbookManager(os.getenv("EXCEL_FILE_PATH")) as active_wb_manager:
#         active_proposal_sheet_manager = active_wb_manager["Proposal - Template"]
#         active_attachments_sheet_manager = active_wb_manager["Attachments - Template"]

#         source_wb = request_file_path("Enter the path of the workbook whose attachments will be merged with the active workbook: ", [".xlsx"])
#         source_wb_manager = WorkbookManager(source_wb).__enter__()
#         source_attachments_sheet_manager = source_wb_manager["Attachments - Template"]

#         grants = active_proposal_sheet_manager.df[["proposalLegacyNumber", "projectLegacyNumber", "OAR Status"]]
#         for index, row in grants.iterrows():
#             grant_pln = row['projectLegacyNumber']
#             grant_id = row['proposalLegacyNumber']

#             active_grant_attachments_ref = active_attachments_sheet_manager.find({ "projectLegacyNumber": grant_pln, "legacyNumber": grant_id })
#             active_grant_attachments = active_grant_attachments_ref.to_dict(orient='records') if not active_grant_attachments_ref.empty else []

#             source_grant_attachments_ref = source_attachments_sheet_manager.find({ "projectLegacyNumber": grant_pln, "legacyNumber": grant_id })
#             source_grant_attachments = source_grant_attachments_ref.to_dict(orient='records') if not source_grant_attachments_ref.empty else []
            
#             appended_attachments = []
#             for attachment in source_grant_attachments:
#                 exists = any(item.get('filePath') == attachment.get('filePath') for item in active_grant_attachments)
#                 if not exists:
#                     appended_attachments.append(attachment)

#             previously_missing = None
#             for index, item in active_grant_attachments_ref.iterrows():
#                 if item.get('filePath') == "MISSING":
#                     previously_missing = index
#             if appended_attachments:
#                 if previously_missing is not None:
#                     active_attachments_sheet_manager.delete_row(previously_missing)

#                 for item in appended_attachments:
#                     next_row = active_attachments_sheet_manager.df.shape[0]
#                     active_attachments_sheet_manager.append_row({
#                         "projectLegacyNumber": grant_pln,
#                         "form": item.get('form'),
#                         "legacyNumber": grant_id,
#                         "attachment type": item.get('attachment type'),
#                         "filePath": item.get('filePath')
#                     })
#             elif not active_grant_attachments:
#                 if previously_missing is None:
#                     next_row = active_attachments_sheet_manager.df.shape[0]
#                     active_attachments_sheet_manager.add_issue(next_row, "projectLegacyNumber", "error", "Grant is missing attachments.")
#                     active_attachments_sheet_manager.append_row({
#                         "projectLegacyNumber": grant_pln,
#                         "legacyNumber": grant_id,
#                         "filePath": "MISSING"
#                     })

#             # if row['OAR Status'] == "Funded":
#             #     active_grant_attachments_ref = active_attachments_sheet_manager.find({ "projectLegacyNumber": grant_pln, "legacyNumber": f"{grant_id}-award" })
#             #     active_grant_attachments = active_grant_attachments_ref.to_dict(orient='records') if not active_grant_attachments_ref.empty else {}

#             #     source_grant_attachments_ref = source_attachments_sheet_manager.find({ "projectLegacyNumber": grant_pln, "legacyNumber": f"{grant_id}-award" })
#             #     source_grant_attachments = source_grant_attachments_ref.to_dict(orient='records') if not source_grant_attachments_ref.empty else {}
                
#             #     appended_attachments = []
#             #     for attachment in source_grant_attachments:
#             #         exists = any(item.get('filePath') == attachment.get('filePath') for item in active_grant_attachments)
#             #         if not exists:
#             #             appended_attachments.append(attachment)

#             #     if appended_attachments:
#             #         for item in appended_attachments:
#             #             active_attachments_sheet_manager.append_row({
#             #                 "projectLegacyNumber": grant_pln,
#             #                 "form": item.get('form'),
#             #                 "legacyNumber": f"{grant_id}-award",
#             #                 "attachment type": item.get('attachment type'),
#             #                 "filePath": item.get('filePath')
#             #             })
#             #             next_row += 1
#             #     elif not active_grant_attachments:
#             #         active_attachments_sheet_manager.add_issue(next_row, "projectLegacyNumber", "error", "Grant is missing attachments.")
#             #         active_attachments_sheet_manager.append_row({
#             #             "projectLegacyNumber": grant_pln,
#             #             "legacyNumber": grant_id,
#             #         })
#             #         next_row
        
#         active_wb_manager.set_write_path("C:/Users/reyhe/OneDrive/Documents/JJay/data_pull_2025_05_23/accumulator_3 - Copy.xlsx")
#         active_wb_manager._save_data()

def merge_attachments():
    with WorkbookManager(os.getenv("EXCEL_FILE_PATH")) as active_wb_manager:
        active_proposal_sheet_manager = active_wb_manager["Proposal - Template"]
        active_attachments_sheet_manager = active_wb_manager["Attachments - Template"]

        source_wb = request_file_path(
            "Enter the path of the workbook whose attachments will be merged with the active workbook:",
            [".xlsx"]
        )

        with WorkbookManager(source_wb) as source_wb_manager:
            source_attachments_sheet_manager = source_wb_manager["Attachments - Template"]

            # Normalize ID columns in both sheets
            for sheet_manager in [active_attachments_sheet_manager, source_attachments_sheet_manager]:
                sheet_manager.df["projectLegacyNumber"] = sheet_manager.df["projectLegacyNumber"].astype(str).str.strip()
                sheet_manager.df["legacyNumber"] = sheet_manager.df["legacyNumber"].astype(str).str.strip()

            grants = active_proposal_sheet_manager.df[["proposalLegacyNumber", "projectLegacyNumber", "OAR Status"]]

            for _, row in grants.iterrows():
                grant_pln = str(row['projectLegacyNumber']).strip()
                grant_id_base = str(row['proposalLegacyNumber']).strip()

                # Decide whether to include award variant
                legacy_ids = [f"{grant_id_base}-award", grant_id_base] if str(row["OAR Status"]).strip().lower() == "funded" else [grant_id_base]

                for grant_id in legacy_ids:
                    active_grant_attachments_ref = active_attachments_sheet_manager.find({
                        "projectLegacyNumber": grant_pln,
                        "legacyNumber": grant_id
                    })
                    active_grant_attachments = active_grant_attachments_ref.to_dict(orient='records') if not active_grant_attachments_ref.empty else []

                    source_grant_attachments_ref = source_attachments_sheet_manager.find({
                        "projectLegacyNumber": grant_pln,
                        "legacyNumber": grant_id
                    })
                    source_grant_attachments = source_grant_attachments_ref.to_dict(orient='records') if not source_grant_attachments_ref.empty else []

                    appended_attachments = []
                    for attachment in source_grant_attachments:
                        exists = any(item.get('filePath') == attachment.get('filePath') for item in active_grant_attachments)
                        if not exists:
                            appended_attachments.append(attachment)

                    previously_missing = next(
                        (i for i, item in active_grant_attachments_ref.iterrows()
                         if str(item.get('filePath', '')).strip().upper() == "MISSING"),
                        None
                    )

                    if appended_attachments:
                        if previously_missing is not None:
                            active_attachments_sheet_manager.delete_row(previously_missing)

                        for item in appended_attachments:
                            active_attachments_sheet_manager.append_row({
                                "projectLegacyNumber": grant_pln,
                                "form": item.get('form'),
                                "legacyNumber": grant_id,
                                "attachment type": item.get('attachment type'),
                                "filePath": item.get('filePath')
                            })

                    elif not active_grant_attachments and previously_missing is None:
                        next_row = active_attachments_sheet_manager.df.shape[0]
                        active_attachments_sheet_manager.add_issue(
                            next_row,
                            "projectLegacyNumber",
                            "error",
                            "Grant is missing attachments."
                        )
                        active_attachments_sheet_manager.append_row({
                            "projectLegacyNumber": grant_pln,
                            "legacyNumber": grant_id,
                            "filePath": "MISSING"
                        })

        # Save workbook
        active_wb_manager.set_write_path("C:/Users/reyhe/OneDrive/Documents/JJay/data_pull_2025_05_23/accumulator_3 - Copy.xlsx")
        active_wb_manager._save_data()



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
            print(f"Sheet Name: {sheet_name}")
            record_identifiers = multi_select_input("Select columns to use as identifiers", shared_columns, "Skip Sheet")

            if not record_identifiers:
                continue

            check_columns = multi_select_input("Select columns to check changes", [col for col in shared_columns if col not in record_identifiers])
            sheet_differences = source_sheet_manager.find_differences(target_sheet_manager, record_identifiers, checking_cols=check_columns)

            if not sheet_differences:
                continue
            if not modified:
                modified = True

            overwrite = request_user_confirmation("Overwrite populated cells(y/n):")

            for index, changes in sheet_differences.items():
                if changes:
                    row = source_sheet_manager.format_df(source_sheet_manager[index]).to_dict()
                    overwrite_changes = {}
                    fill_changes = {}
                    for key, val in changes.items():
                        if row[key] is None:
                            fill_changes[key] = val
                        else:
                            overwrite_changes[key] = val
                    
                    if fill_changes:
                        source_sheet_manager.update_cell(index, fill_changes)
                    if overwrite_changes:
                        if overwrite:
                            source_sheet_manager.update_cell(index, overwrite_changes)
                            for key in overwrite_changes.keys():
                                source_sheet_manager.add_issue(index, key, "notice", f"Value was changed from: {row.get(key)}")
                        else:
                            for key in overwrite_changes.keys():
                                source_sheet_manager.add_issue(index, key, "notice", f"Value differs in reference sheet: {overwrite_changes.get(key)}")

        if modified and source_wb.set_write_path(input("Input file save path:")):
            source_wb._save_data()

def manage_migration():
    print(f"Current Process: {"Manage Migration"}")
    while True:
        user_selection = single_select_input("Select a Migration Manager Action", [
            "Generate Data",
            "Generate Attachments",
            "Compile Changes",
            "Exit Process"
        ])

        match user_selection:
            case "Generate Data":
                generate_data()
            case "Generate Attachments":
                merge_attachments()
            case "Compile Changes":
                compile_changes()
            case _:
                return