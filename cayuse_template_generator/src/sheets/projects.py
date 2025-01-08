from classes.SheetManager import SheetManager

SHEET_NAME = "Proposal - Template"
SHEET_COLUMNS = ["projectLegacyNumber", "title", "status"]

def populate_template_title(self):
    print('method 1')
    pass

def populate_template_status(self):
    print('method 2')
    pass

def populate_template_oar_status(self):
    print('method 3')
    pass

def append_to_sheet(grant) -> dict:
    row_data = dict()
    row_data = {"projectLegacyNumber": [123], "title": ["hehehehe"], "status": ["Testing"]}
    return row_data

project_sheet_manager = SheetManager(SHEET_NAME, SHEET_COLUMNS, append_to_sheet)