import pandas as pd
from pathlib import Path
import openpyxl

from ..log_manager import LogManager
from . import SheetManager

class WorkbookManager:
    sheets = {}

    def __init__(self, read_file_path: str = None):
        if read_file_path and not Path(read_file_path).exists():
            raise ValueError(f"Workbook file does not exist at path: {read_file_path}")

        self.read_file_path = read_file_path

    def __enter__(self):
        if self.read_file_path:
            excel_obj = pd.ExcelFile(self.read_file_path)

            for sheet_name in excel_obj.sheet_names:
                self.sheets[sheet_name] = SheetManager(excel_obj.parse(sheet_name))

            read_path_obj = Path(self.read_file_path)
            log_file_path = read_path_obj.parent / f"{read_path_obj.stem}_workbook_logs.json"
            self.log_manager = LogManager(log_file_path).__enter__()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def _save_data(self, write_path: str):
        if not write_path:
            raise ValueError("Missing file write path")
        
        try:
            # Load existing workbook if available, otherwise create new one
            wb = openpyxl.load_workbook(self.read_file_path) if self.read_file_path else openpyxl.Workbook()
            for sheet_name, df_sheet in self.sheets.items():
                if sheet_name not in wb.sheetnames:
                    created_sheet = wb.create_sheet(sheet_name)
                    created_sheet.append(list(df_sheet.df.columns))
                
                df_sheet._append_data(wb[sheet_name])
            wb.save(write_path)    
        except Exception as err:
            raise Exception(f"Error occured while attempting to save Workbook data: {err}")