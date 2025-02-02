import os
import pandas as pd
import openpyxl

from packages.workbook_manager import WorkbookManager


class ReportGenerator:
    process_name = "Report Generator"
    
    def __init__(self, save_path):
        self.save_path = save_path
        self.generated_reports = {}
        
    def __enter__(self):
        self.report_workbook = WorkbookManager()
        self.report_workbook.create_sheet("report_meta_data", ["sheet_name", "table", "record_identifier"])
        
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        if self.get_num_reports():
            save_location = os.path.join(self.save_path, "generated_report.xlsx")
            self.report_workbook.save_changes(save_location)
            
        print("Report successfully generated.")
    
    def append_report(self, report_name: str, table: str, record_identifier: str, report_data: list[dict]):
        self.report_workbook.create_sheet(report_name, report_data)
        self.report_workbook.append_row("report_meta_data", {
            "sheet_name": report_name,
            "table": table,
            "record_identifier": record_identifier
        })
        
    def get_num_reports(self):
        return len([item for item in self.report_workbook.df.keys() if item != "report_meta_data"])

        
    
# Process will provide files, classes will only log if path to file was provided