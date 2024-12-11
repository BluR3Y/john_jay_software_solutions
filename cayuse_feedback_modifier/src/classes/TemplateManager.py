import os
import pandas as pd

from classes.LogManager.TemplateLogManager import TemplateLogManager

class TemplateManager:

    def __init__(self, read_file_path, log_file_path):
        if os.path.exists(read_file_path):
            # Read the contents in the workbook
            self.df = pd.read_excel(read_file_path, sheet_name=None)
            self.log_manager = TemplateLogManager(log_file_path)
        else:
            raise Exception("The Template manager was provided an invalid file path.")
        
    def update_cell(self, process_name, sheet_name, row, col, new_val):
        if sheet_name in list(self.df.keys()):
            sheet_data_frame = self.df[sheet_name]
            cell_prev_value = sheet_data_frame.iloc[row][col]
            sheet_data_frame.loc[row, col] = new_val
            self.log_manager.append_log(
                process_name,
                sheet_name,
                row,
                col,
                cell_prev_value,
                new_val
            )
        else:
            raise Exception(f"The sheet with the name '{sheet_name}' does not exist in the workbook.")
        
    def save_changes(self, write_file_path, index=False):
        # Use ExcelWriter to write multiple sheets back into the Excel file
        with pd.ExcelWriter(write_file_path, engine='openpyxl', mode='w') as writer:
            for sheet_name, df_sheet in self.df.items():
                # Leave index as False if you don't want to save the index column from the DataFrame
                df_sheet.to_excel(writer, sheet_name=sheet_name, index=index)
        
        # Save logger changes
        self.log_manager.save_logs()