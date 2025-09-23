
from packages.wb_manager import WorkbookManager
from packages.data_manager import load_config
import json

# def test_env():
#     print("Welcome To Test Environment!")
#     with WorkbookManager("C:/Users/reyhe/OneDrive/Desktop/data_set_1_associated_sponsors.xlsx") as wb_manager:
#         print(wb_manager.list_sheets())

#         data_sheet = wb_manager.get_sheet("data_set_1_sponsors")
#         print(data_sheet.find({"Grant_ID": 93411}))
#         print(data_sheet.match({"Sponsor_1": "City University of New York (CUNY)"}))
#         data_sheet.append_row({
#             "Grant_ID": 69420,
#             "Sponsor_1": "Limp Bizkit"
#         })
#         wb_manager._dirty = True
#         data_sheet.add_annotation(3, "Grant_ID", "info", "Hello There!!")

#         wb_manager.set_write_path("C:/Users/reyhe/OneDrive/Desktop/data_set_1_associated_sponsor_test_save.xlsx")

# def test_env():
#     print("Welcome to Test Environment!")
#     cfg_path = r"C:/Users/reyhe/OneDrive/Documents/GitHub/john_jay_software_solutions/src/assets/test_data_manager_config.json"
#     with open(cfg_path, "r", encoding="utf-8") as f:
#         cfg = json.load(f)
#     run_with_config(cfg)

def test_env():
    print("Welcome to Test Environment!")
    load_config("C:/Users/reyhe/OneDrive/Documents/GitHub/john_jay_software_solutions/src/assets/data_manager_v2_config.json")