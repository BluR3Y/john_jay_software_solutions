import os

from packages.database_manager import DatabaseManager
from packages.migration_manager import MigrationManager

PROCESS_NAME = "Migration Manager"

def manage_migration(db_path: str):
    with DatabaseManager(db_path, PROCESS_NAME) as db_manager:
        with MigrationManager(db_manager, os.getenv('EXCEL_FILE_PATH'), os.getenv('SAVE_PATH')) as migration_manager:
            existing_grants = migration_manager.feedback_template_manager.df["Proposal - Template"]['proposalLegacyNumber'].tolist()
            
            query_grant_ids = db_manager.select_query(
                table="grants",
                cols=["Grant_ID"],
                limit=3000
            )
            
            categorized_grants = [(grant['Grant_ID'], grant['Grant_ID'] in existing_grants) for grant in query_grant_ids]

            for grant_id, exists in categorized_grants:
                if exists:
                    continue
                
                select_grant_query = db_manager.select_query(
                    table="grants",
                    conditions={
                        "Grant_ID": {
                            "operator": "=",
                            "value": grant_id
                        }
                    }
                )[0]
                try:
                    migration_manager.projects_sheet_append(select_grant_query, exists)
                except Exception as err:
                    print(f"Error while adding to projects sheet: {err}")
                
                select_pi_query = db_manager.select_query(
                    table="PI_name",
                    conditions={
                        "PI_Grant_ID": {
                            "operator": "=",
                            "value": grant_id
                        }
                    }
                )
                try:
                    migration_manager.members_sheet_append(select_grant_query, select_pi_query, exists)
                except Exception as err:
                    print(f"Error while adding to memebers sheet: {err}")
                
                select_total_query = db_manager.select_query(
                    table="total",
                    conditions={
                        "RFunds_Grant_ID": {
                            "operator": "=",
                            "value": grant_id
                        }
                    }
                )
                select_ri_funds_query = db_manager.select_query(
                    table="RIfunds",
                    conditions={
                        "RIFunds_Grant_ID": {
                            "operator": "=",
                            "value": grant_id
                        }
                    }
                )
                try:
                    migration_manager.proposals_sheet_append(select_grant_query, select_total_query, select_ri_funds_query, exists)
                except Exception as err:
                    print(f"Error while adding to proposals sheet: {err}")
                
                # select_dates_query = db_manager.select_query(
                #     table="Dates",
                #     conditions={
                #         "Date_GrantID": {
                #             "operator": "=",
                #             "value": grant_id
                #         }
                #     }
                # )
                # select_dates_query = (select_dates_query[0] if len(select_dates_query) else {})
                # select_costshare_query = db_manager.select_query(
                #     table="CostShare",
                #     conditions={
                #         "GrantID": {
                #             "operator": "=",
                #             "value": grant_id
                #         }
                #     }
                # )
                # select_ffunds_query = db_manager.select_query(
                #     table="Ffunds",
                #     conditions={
                #         "FFunds_Grant_ID": {
                #             "operator": "=",
                #             "value": grant_id
                #         }
                #     }
                # )
                # select_fifunds_query = db_manager.select_query(
                #     table="FIFunds",
                #     conditions={
                #         "FIFunds_Grant_ID": {
                #             "operator": "=",
                #             "value": grant_id
                #         }
                #     }
                # )
                # if select_grant_query['Status'] == "Funded" or select_grant_query['RF_Account'] != None:
                #     try:
                #         migration_manager.awards_sheet_append(select_grant_query, select_dates_query, select_total_query, select_ri_funds_query, select_costshare_query, select_ffunds_query, select_fifunds_query, exists)
                #     except Exception as err:
                #         print(f"Error occured while adding to awards sheet: {err}")