import os
from tqdm import tqdm

from packages.database_manager import DatabaseManager
from packages.migration_manager import MigrationManager
from packages.workbook_manager import WorkbookManager
from modules.utils import multi_select_input, single_select_input, request_file_path

PROCESS_NAME = "Migration Manager"

def generate_data(db_path: str):
    with DatabaseManager(db_path, PROCESS_NAME) as db_manager:
        with MigrationManager(db_manager, os.getenv('EXCEL_FILE_PATH')) as migration_manager:
            # existing_grants = [int(gt) for gt in migration_manager.feedback_template_manager.df["Proposal - Template"]['proposalLegacyNumber'].tolist()]
            existing_wb = WorkbookManager("C:/Users/reyhe/OneDrive/Documents/JJay/data_pull_2025_04_17/latest_generated_data_set_2_18_04_2025.xlsx")
            existing_grants = [int(gt) for gt in existing_wb.df["Proposal - Template"]['proposalLegacyNumber'].tolist()]

            # query_grant_ids = db_manager.select_query(
            #     table="grants",
            #     cols=["Grant_ID"],
            #     conditions={
            #         "End_Date_Req": {
            #             "operator": ">",
            #             "value": "2016-12-31"
            #         }
            #     }
            # )
            # grant_ids = [grant['Grant_ID'] for grant in query_grant_ids if grant['Grant_ID'] not in existing_grants]
            for grant_id in tqdm(existing_grants, "Processing grants", unit="grant"):
                
                # Retrieve primary grant data
                select_grant_query = db_manager.select_query(
                    table="grants",
                    conditions={
                        "Grant_ID": {
                            "operator": "=",
                            "value": grant_id
                        }
                    }
                )
                if (not select_grant_query):
                    print(f"Could not find grant: {grant_id}")
                    continue
                select_grant_query = select_grant_query[0]
                print(select_grant_query["Status"])
                
                # Append grant to "projects" sheet
                try:
                    migration_manager.projects_sheet_append(select_grant_query)
                except Exception as err:
                    print(f"Error while adding to projects sheet: {err}")
                
                # Retrieve "primary investigator" records relating to grant
                select_pi_query = db_manager.select_query(
                    table="PI_name",
                    conditions={
                        "PI_Grant_ID": {
                            "operator": "=",
                            "value": grant_id
                        }
                    }
                )
                # Append grant to "members" sheet
                try:
                    migration_manager.members_sheet_append(select_grant_query, select_pi_query)
                except Exception as err:
                    print(f"Error while adding to members sheet: {err}")
                
                # Retrieve "financial" records relating to grant
                select_total_query = db_manager.select_query(
                    table="total",
                    conditions={
                        "RFunds_Grant_ID": {
                            "operator": "=",
                            "value": grant_id
                        }
                    }
                )
                # Retrieve "ri funds" records relating to grant
                select_ri_funds_query = db_manager.select_query(
                    table="RIfunds",
                    conditions={
                        "RIFunds_Grant_ID": {
                            "operator": "=",
                            "value": grant_id
                        }
                    }
                )
                
                # Append grant to "proposals" sheet
                try:
                    migration_manager.proposals_sheet_append(select_grant_query, select_total_query, select_ri_funds_query)
                except Exception as err:
                    print(err)
                    print(f"Error while adding to proposals sheet: {err}")
                
                # Retrieve "updates" records relating to grant
                select_dates_query = db_manager.select_query(
                    table="Dates",
                    conditions={
                        "Date_GrantID": {
                            "operator": "=",
                            "value": grant_id
                        }
                    }
                )
                
                # Retrieve "constshare" records relating to grant
                select_costshare_query = db_manager.select_query(
                    table="CostShare",
                    conditions={
                        "GrantID": {
                            "operator": "=",
                            "value": grant_id
                        }
                    }
                )
                
                # Retrieve "f funds" records relating to grant
                select_ffunds_query = db_manager.select_query(
                    table="Ffunds",
                    conditions={
                        "FFunds_Grant_ID": {
                            "operator": "=",
                            "value": grant_id
                        }
                    }
                )
                
                # Retrieve "fi funds" relating to grant
                select_fifunds_query = db_manager.select_query(
                    table="FIFunds",
                    conditions={
                        "FIFunds_Grant_ID": {
                            "operator": "=",
                            "value": grant_id
                        }
                    }
                )
                
                # If grant is funded or has an 'RF_Account' number, all funded grants are assigned one:
                if select_grant_query['Status'] == "Funded" or select_grant_query['RF_Account'] != None:
                    # Append grant to "awards" sheet
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
                        print(f"Error occured while appending to awards sheet: {err}")
                    
                    # Append grant to "attachments" sheet
                    try:
                        migration_manager.attachments_sheet_append(select_grant_query)
                    except Exception as err:
                        print(f"Error occured while appending to attachments sheet: {err}")

def merge_workbooks(base_path: str):
    with WorkbookManager(
        read_file_path=base_path,
        # write_file_path=os.path.join(os.path.dirname(base_path), f"{os.path.basename(base_path).split('.')[0]}_merged_workbook.xlsx")
    ) as base_wb:
        updates_path = request_file_path("Enter the file path of the updated workbook: ", [".xlsx"])
        updates_wb = WorkbookManager(updates_path).__enter__()

        non_empty_props = lambda x: {key:val for key,val in x.items() if (val)}

        selected_sheets = multi_select_input("Select which sheets to apply updates: ", list(updates_wb.df.keys()))
        sheet_identifier = "projectLegacyNumber"
        errors = []
        for sheet in selected_sheets:

            for updated_row in updates_wb.get_sheet(sheet, format=True, orient='records'):
                row_id = updated_row.get(sheet_identifier)
                id_search_ref = base_wb.find(sheet, {sheet_identifier: row_id})
                if id_search_ref is None or id_search_ref.empty:
                    continue

                closest_match = base_wb.find_closest_row(updated_row, id_search_ref, 0.65)
                if closest_match is None or closest_match.empty:
                    continue
                match_dict = base_wb.formatDF(closest_match).to_dict()
                try:
                    base_wb.update_cell(
                        PROCESS_NAME,
                        sheet,
                        closest_match,
                        {
                            key:prop for key,prop in non_empty_props(updated_row).items()
                            if match_dict.get(key) != prop
                        }
                    )
                except Exception as err:
                    errors.append(f"Error occured while updating grant {row_id}: {err}")
        if len(errors):
            print('\n'.join(errors))
    

def manage_migration(db_path: str):
    print(f"Current Process:{PROCESS_NAME}")
    while True:
            user_selection = single_select_input("Select a Database Manager Action:",[
                "Migrate Data",
                "Merge Workbooks",
                "Exit Process"
            ])

            match user_selection:
                case "Migrate Data":
                    generate_data(db_path)
                case "Merge Workbooks":
                    merge_workbooks(os.getenv("EXCEL_FILE_PATH"))
                case _:
                    return