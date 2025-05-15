import os
from tqdm import tqdm

from packages.migration_manager import MigrationManager

def manage_migration():
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
            },
            limit=20
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

            # Append grant to "Proposals" sheet
            try:
                migration_manager.proposals_sheet_append(select_grant_query, select_total_query, select_ri_funds_query)
            except Exception as err:
                migration_manager.generated_wb_manager["Errors"].append_row({
                    "Grant_ID": grant_id,
                    "Sheet": "Proposal - Template",
                    "Issue": f"Error while adding to projects sheet: {err}"
                })

            # # Retrieve Primary Investigator records relating to grants
            # select_pi_query = migration_manager.db_manager.select_query(
            #     table="PI_name",
            #     conditions={
            #         "PI_Grant_ID": {
            #             "operator": "=",
            #             "value": grant_id
            #         }
            #     }
            # )

            # # Retrieve "Updates" records relating to grant
            # select_dates_query = migration_manager.db_manager.select_query(
            #     table="Dates",
            #     conditions={
            #         "Date_GrantID": {
            #             "operator": "=",
            #             "value": grant_id
            #         }
            #     }
            # )
            # # Retrieve "costshare" records relating to grant
            # select_costshare_query = migration_manager.db_manager.select_query(
            #     table="CostShare",
            #     conditions={
            #         "GrantID": {
            #             "operator": "=",
            #             "value": grant_id
            #         }
            #     }
            # )
            # # Retrieve "F funds" records relating to grant
            # select_ffunds_query = migration_manager.db_manager.select_query(
            #     table="Ffunds",
            #     conditions={
            #         "FFunds_Grant_ID": {
            #             "operator": "=",
            #             "value": grant_id
            #         }
            #     }
            # )
            # # Retrieve "FI funds" relating to grant
            # select_fifunds_query = migration_manager.db_manager.select_query(
            #     table="FIFunds",
            #     conditions={
            #         "FIFunds_Grant_ID": {
            #             "operator": "=",
            #             "value": grant_id
            #         }
            #     }
            # )