import os
from tqdm import tqdm

from packages.database_manager import DatabaseManager
from packages.migration_manager import MigrationManager

PROCESS_NAME = "Migration Manager"

def manage_migration(db_path: str):
    with DatabaseManager(db_path, PROCESS_NAME) as db_manager:
        with MigrationManager(db_manager, os.getenv('EXCEL_FILE_PATH'), os.getenv('SAVE_PATH')) as migration_manager:
            existing_grants = [int(gt) for gt in migration_manager.feedback_template_manager.df["Proposal - Template"]['proposalLegacyNumber'].tolist()]
            
            query_grant_ids = db_manager.select_query(
                table="grants",
                cols=["Grant_ID"]
            )
            grant_ids = [grant['Grant_ID'] for grant in query_grant_ids]
            
            # Append Existing grants
            append_existing = True
            # Append Non-Existing grants
            append_new = False

            for grant_id in tqdm(existing_grants, "Processing grants", unit="grant"):
                exists = grant_id in existing_grants
                if (exists and not append_existing) or (not exists and not append_new):
                    continue
                
                # Retrieve primary grant data
                select_grant_query = db_manager.select_query(
                    table="grants",
                    conditions={
                        "Grant_ID": {
                            "operator": "=",
                            "value": grant_id
                        }
                    }
                )[0]
                
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
                    print(f"Error while adding to memebers sheet: {err}")
                
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