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
                "Grant_ID": {
                    "operator": "IN",
                    "value": [92654,
92871,
92872,
92786,
92920,
93559,
92853,
93003,
92906,
93405,
93430,
93453,
93445,
92992,
93443,
93444,
93446,
93542,
93543,
93448,
93460,
93526,
92938,
93521,
93533,
93539,
93413,
93414,
93415,
93031,
93032,
93422,
93424,
93425,
93428,
93429,
93432,
93434,
93435,
93436,
93437,
93438,
93440,
93441,
93442,
93531,
93560,
93548,
93529,
93530,
93566,
93527,
93545,
93641,
93568,
93528,
93633,
93757,
93756,
93758,
93759,
93760,
93761,
93762,
93763,
93764,
93611,
93622,
93770,
93802,
93769,
93784,
93785,
93786,
93787,
93788,
93780,
93783,
93610,
93781,
93782,
93790,
93791,
93792,
93793,
93794,
93634,
93631,
93799,
93747,
93750,
93752,
93754,
93765,
93835,
93836,
93837,
93838,
93839,
93840,
93841,
93847,
93848,
93635,
93795,
93755,
93834,
93638,
93815,
93643,
93842,
93843,
93844,
93845,
93846,
93625,
93875,
93876,
93886,
93871,
93872,
93873,
93874,
93887,
93888,
93889,
93879,
93800,
93858,
93997,
93998,
93999,
94000,
94001,
94002,
93920,
93771,
93923,
93921,
93804,
93821,
93822,
94003,
94004,
94005,
94006,
93857,
93863,
93931,
94007,
94009,
94011,
94012,
94013,
94014,
93779,
94015,
94016,
94017,
94018,
94019,
94020,
94021,
93881,
94022,
94023,
94024,
93948,
94025,
94041,
94042,
94043,
94044,
94066,
94045,
94046,
93953,
94063,
94064,
94065,
94067,
94167,
94068,
94069,
94071,
94089,
94070,
94179,
94180,
94181,
94182,
94183,
94184,
94148,
94149,
94150,
94151,
93933,
93937,
94143,
94144,
94145,
94146,
94147,
93930,
94035,
94165,
94166,
941642,
93989,
94029,
94030,
94033,
94036,
94039,
94049,
94050,
94088,
94169,
94170,
94171,
94172,
94173,
94174,
94175,
94176,
94177,
94178,
93946,
94190,
94191,
94192,
94193,
94194,
94195,
94185,
94196,
94197,
94198,
94226,
94233,
93957,
93962,
94234,
94222,
94224,
94225,
94227,
93952,
94031,
94290,
94291,
94292,
94293,
94294,
94289,
94285,
94287,
94288,
94286,
94266,
94282,
94283,
94284,
94216,
94133,
94136,
94137,
94156,
94281,
94279,
94134,
94219,
94278,
94121,
94200,
94008,
94311,
94312,
94313,
94314,
94315,
94275,
94335,
94457,
94458,
94324,
94459,
94460,
94334,
94342,
94343,
94344,
94461,
94463,
94464,
94331,
94333,
94379,
94345,
94465,
94466,
94467,
94468,
94469,
94255,
94228,
94232,
94246,
94310,
94471,
94472,
94475,
94476,
94477,
94478,
94479,
94490,
94480,
94481,
94209,
94254,
94462,
94493,
94491,
94274,
94277,
94499,
94500,
94501,
94502,
94503,
94520,
94521,
95418,
94577,
94299,
94309,
94318,
94322,
94358,
94376,
94551,
94552,
94553,
94554,
94555,
94556,
94557,
94547,
94548,
94549,
94550,
94272,
94295,
94572,
94273,
94321,
94323,
94328,
94340,
94637,
94638,
94336,
94337,
94338,
94332,
94636,
94386,
94563,
94635,
94610,
94634,
94598,
94609,
94537,
94051,
94523,
94417,
94581,
94507,
94628,
94492,
94573,
94536,
94570,
94571,
96475,
94569,
94698,
94624,
94643,
94794,
94795,
94671,
94327,
94876,
94874,
94719,
94862,
94819,
94907,
94806,
94820,
94846,
94801,
94990,
95096,
95140,
95141,
98001,
94992,
95059,
94723,
94782,
95199,
95120,
95182,
95060,
95203,
95000,
95238,
95057,
95317,
93907,
95787,
95344,
95367,
95431,
95664,
95790,
95791,
95769,
95770,
95792,
95793,
95989,
95987,
95988,
95745,
95733,
95734,
95746,
95403,
94329,
94544,
95747,
95092,
95742,
95150,
94968,
95981,
95748,
95749,
95750,
95815,
95346,
95735,
95751,
95763,
95764,
95771,
95992,
95993,
95994,
95772,
95816,
95817,
95818,
95819,
95736,
95773,
95820,
95821,
95752,
95756,
95730,
95737,
95753,
95755,
95822,
95823,
95982,
95774,
95781,
95824,
95983,
95995,
95424,
95526,
95335,
95345,
95731,
95765,
95782,
95783,
95996,
95998,
95999,
95739,
95743,
95757,
95825,
96001,
95834,
95740,
95758,
95759,
95784,
95826,
95835,
95984,
95985,
96000,
95986,
95732,
95760,
95744,
95762,
95768,
95785,
95786,
95836,
95741,
95761,
95788,
95789,
95980,
95587,
95515,
95640,
95589,
95588,
95574,
95575,
95576,
95577,
95579,
95580,
95581,
95582,
95583,
95584,
95585,
95586,
94891,
95623,
95593,
95594,
95595,
95597,
95598,
95599,
95645,
95596,
95697,
95699,
95700,
95662,
95690,
95698,
95691,
95692,
95693,
95694,
95695,
95696,
96133,
95720,
95722,
95728,
95727,
95724,
95725,
95726,
95766,
95767,
95775,
95776,
95777,
95778,
95779,
95780,
95813,
95814,
95827,
95829,
95830,
95831,
95832,
95833,
95848,
95849,
95850,
95851,
95847,
95903,
95906,
95907,
95908,
95909,
95878,
95886,
95963,
95964,
95965,
95966,
95962,
95958,
95959,
95960,
95961,
95977,
95971,
95972,
95973,
95974,
95975,
96017,
96018,
96019,
96020,
96021,
96022,
96023,
96015,
96016,
96038,
96039,
96061,
96062,
96050,
96063,
96064,
96065,
96066,
96068,
96060,
96054,
96055,
96056,
96057,
96058,
96059,
96071,
96072,
96076,
96086,
96073,
96074,
96075,
96093,
96113,
96114,
94832,
95402,
95715,
95711,
96078,
95842,
95679,
92758,
92765,
92728,
92793,
92791,
92842,
92845,
92848,
92849,
92867,
92883,
92884,
92922,
92784,
92972,
92929,
92932,
92933,
92934,
92966,
92969,
92960,
92868,
92946,
92800,
92864,
95671,
95652,
95625,
95602,
95653,
95913,
95905,
96032,
95997,
96093,
96110,
94833,
95547,
95626,
95663,
95712,
96012]
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
            # if not select_total_query:
            #     migration_manager.generated_wb_manager["Errors"].append_row({
            #         "Grant_ID": grant_id,
            #         "Sheet": "Management",
            #         "Issue": f"Could not find record for grant in table 'total'"
            #     })
            #     continue
            
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
            # if not select_ri_funds_query:
            #     migration_manager.generated_wb_manager["Errors"].append_row({
            #         "Grant_ID": grant_id,
            #         "Sheet": "Management",
            #         "Issue": f"Could not find record for grant in table 'RIfunds'"
            #     })
            #     continue

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
            # if not select_pi_query:
            #     migration_manager.generated_wb_manager["Errors"].append_row({
            #         "Grant_ID": grant_id,
            #         "Sheet": "Members",
            #         "Issue": f"Could not find record for grant in table 'PI_name'"
            #     })
            #     continue

            # Append grant to "Members" sheet
            try:
                migration_manager.members_sheet_append(select_grant_query)
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