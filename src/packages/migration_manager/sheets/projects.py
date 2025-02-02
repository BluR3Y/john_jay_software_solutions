
from sheets.sheet import Sheet
from workbook_manager import WorkbookManager

def ProjectSheet(Sheet):
    SHEET_NAME = "Project - Template"
    SHEET_COLUMNS = ["projectLegacyNumber", "title", "status"]
    
    def __init__(self, generated_template_manager: WorkbookManager):
        