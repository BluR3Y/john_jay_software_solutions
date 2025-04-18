import os
import pandas as pd
import openpyxl
import pathlib
import warnings
import numpy as np

from typing import Union

from . import PropertyManager
from ..log_manager import LogManager

class WorkbookManager:
    read_file_path = None
    log_manager = None
    df = {}
    
    def __init__(self, read_file_path: str = None, create_sheets: dict = None):
        if read_file_path:
            if not os.path.exists(read_file_path):
                raise ValueError(f"The WorkbookManager was provided an invalid file path: {read_file_path}")
            
            # Store the file path
            self.read_file_path = read_file_path
            
            # Read the contents of the workbook
            self.df = pd.read_excel(read_file_path, sheet_name=None)
            
            file_path_obj = pathlib.Path(read_file_path)
            log_file_path = os.path.join(file_path_obj.parent, f"{file_path_obj.stem}_workbook_logs.json")
            self.log_manager = LogManager(log_file_path).__enter__()
        elif create_sheets:
            self.df = {sheet_name: pd.DataFrame(sheet_rows) for sheet_name, sheet_rows in create_sheets.items()}
        
        # Initialize an instance of the Comment Manager
        self.property_manager = PropertyManager(read_file_path, self.df.keys())

    def formatDF(self, df: Union[pd.DataFrame, pd.Series]) -> Union[pd.DataFrame, pd.Series]:
        """
        Replace NaT and NaN with None, and convert datetime columns or values to Python datetime objects.
        Works for both Series and DataFrame inputs.
        """
        df = df.replace({pd.NaT: None, np.nan: None})

        if isinstance(df, pd.Series):
            # Convert datetime Series to Python datetimes
            if pd.api.types.is_datetime64_any_dtype(df):
                df = df.apply(lambda x: x.to_pydatetime() if pd.notnull(x) else None)
            return df
        
        for col in df.select_dtypes(include=["datetime64[ns]"]):
            df[col] = df[col].apply(lambda x: x.to_pydatetime() if pd.notnull(x) else None)
        return df

    def get_sheet(self, sheet_name: str, cols: list[str] = None, format = False, orient:str = None):
        if sheet_name not in self.df:
            return None
        
        cols = cols or []
        sheet_df = self.df[sheet_name][cols] if cols else self.df[sheet_name]
        sheet_df = sheet_df.copy()

        if format:
            sheet_df = self.formatDF(sheet_df)
        
        return sheet_df.to_dict(orient) if orient else sheet_df.to_dict()

    def create_sheet(self, sheet_name: str, sheet_columns: list):
        if sheet_name in self.df.keys():
            raise ValueError(f"A sheet with the name '{sheet_name}' already exists in the workbook.")
        
        sheet_data_frame = None
        populated_data = all(isinstance(item, dict) for item in sheet_columns)
        if populated_data:
            sheet_data_frame = pd.DataFrame(sheet_columns)
        else:
            sheet_data_frame = pd.DataFrame(columns=sheet_columns)
            
        self.df[sheet_name] = sheet_data_frame
        self.property_manager.property_store[sheet_name] = {}
    
    def series_indices(self, sheet: str, obj: pd.Series):
        """Return a list of row indices where the Series matches exactly in the given sheet."""
        
        if sheet not in self.df:
            raise ValueError(f"The sheet '{sheet}' does not exist in the workbook.")
        
        sheet_df = self.df[sheet]

        if not isinstance(obj, pd.Series):
            raise TypeError("obj must be a pandas Series")

        # Ensure obj has the same columns as the DataFrame for valid comparison
        if not all(col in sheet_df.columns for col in obj.index):
            raise ValueError("Series contains columns that do not exist in the sheet.")

        matching_indices = sheet_df.index[sheet_df.apply(lambda row: row.equals(obj), axis=1)]
        return matching_indices.tolist()

    def update_cell(self, process: str, sheet: str, row: Union[int, pd.Series], col: Union[int, str], new_val) -> pd.Series:
        """Update a specific cell in a given sheet and log the change."""

        if sheet not in self.df:
            raise ValueError(f"The sheet '{sheet}' does not exist in the workbook.")

        sheet_df = self.df[sheet]

        # Determine row index
        if isinstance(row, pd.Series):
            row_indices = self.series_indices(sheet, row)
            if not row_indices:
                raise ValueError("No matching row found.")
            if len(row_indices) > 1:
                raise ValueError("Multiple matching rows found. Please refine your search criteria.")
            row_index = row_indices[0]
        else:
            if not (0 <= row < sheet_df.shape[0]):  
                raise ValueError("Invalid row index.")
            row_index = row

        # Determine column name
        if isinstance(col, int):
            if not (0 <= col < len(sheet_df.columns)):
                raise ValueError("Invalid column index.")
            col_name = sheet_df.columns[col]
        else:
            if col not in sheet_df.columns:
                raise ValueError("Column not found in sheet.")
            col_name = col

        # Retrieve previous value and update the DataFrame
        cell_prev_value = sheet_df.at[row_index, col_name]
        sheet_df.at[row_index, col_name] = new_val  # Directly update the DataFrame

        # Reassign 'row' to reflect changes
        row = sheet_df.iloc[row_index]

        # Log the change if logging is enabled
        if self.log_manager:
            # self.log_manager.append_runtime_log(process, {sheet:{row_index:{col_name:{"prev_value": cell_prev_value,"new_value": new_val}}}})
            self.log_manager.append_runtime_log(process, "update", sheet, row_index, {col_name: cell_prev_value})

        return row  # Return the updated row     
        
    def append_row(self, sheet: str, props: dict):
        # Create a new DataFrame
        new_row = pd.DataFrame({key: [value] for key, value in props.items()})
        # Append using pd.concat
        self.df[sheet] = pd.concat([self.df[sheet], new_row], ignore_index=True)
        
    def row_follows_condition(self, row, conditions: dict) -> bool:
        for identifier, value in conditions.items():
            if row[identifier] != value:
                return False
        return True
    
    def find(self, sheet_name: str, conditions: dict, return_one: bool = False, to_dict: str = None):
        """
        Retrieve rows from a specified sheet in the workbook that match the given column-value conditions.

        Args:
            sheet_name (str): Name of the sheet to query.
            conditions (dict): Dictionary of {column: value} to filter the DataFrame.
            return_one (bool, optional): If True, return only the first matching row. Defaults to False.
            to_dict (str, optional): If provided, converts result to dictionary using the specified orientation (e.g., 'records').

        Returns:
            pd.DataFrame, dict, or None: Filtered result(s), format depending on `return_one` and `to_dict`.
        """
        
        if sheet_name not in self.df:
            raise ValueError(f"The sheet '{sheet_name}' was not found in the workbook.")
        
        sheet_data_frame = self.df[sheet_name]
        
        # Ensure that conditions refer to existing columns
        invalid_columns = [col for col in conditions if col not in sheet_data_frame.columns]
        if invalid_columns:
            raise KeyError(f"Invalid column names in conditions: {invalid_columns}")
        
        # Apply filtering
        mask = pd.Series(True, index=sheet_data_frame.index)
        for column, value in conditions.items():
            mask &= (sheet_data_frame[column] == value)
        
        filtered_rows = sheet_data_frame[mask]
        
        if filtered_rows.empty:
            return None
        
        formatted = self.formatDF(filtered_rows)
        
        if to_dict:
            formatted = formatted.to_dict(orient=to_dict)
        
        if return_one:
            return formatted[0] if isinstance(formatted, list) else formatted.iloc[0]
        
        return formatted

        # return (filtered_rows.iloc[0] if as_ref else filtered_rows.iloc[0].replace([pd.NaT, np.nan], None).to_dict()) if return_one else (filtered_rows if as_ref else filtered_rows.replace([pd.NaT, np.nan], None).to_dict(orient="records"))
    
    def save_changes(self, write_file_path: str, index=False):
        """
        Saves the data stored in the pandas dataframes by converting each dataframe into an excel sheet in the same workbook.
        Additionally, function also sets the 'sheet_state' property to that of the sheet in the workbook that was imported.
        
        # Parameters:
        - write_file_path: file path where the migration data will be stored.
        - index: Will determine if the index column from the DataFrame will persist in the stored excel sheet.
        """
                
        if write_file_path == self.read_file_path:
            warnings.warn(f"The save path is the same as the read path, meaning that file will be overwritten with changes.")
        
        # populated_sheets = {sheet_name: sheet_content for sheet_name, sheet_content in self.df.items() if not sheet_content.empty}
        is_empty = all([sheet_content.empty for sheet_content in self.df.values()])
        if is_empty:
            print("Workbook is empty. Now exiting Workbook Manager.")
        
        try:
            # Use ExcelWriter to write multiple sheets back into the Excel file
            with pd.ExcelWriter(write_file_path, engine='openpyxl', mode='w') as writer:
                for sheet_name, df_sheet in self.df.items():
                    df_sheet.to_excel(writer, sheet_name=sheet_name, index=index)
                    
            # Save LogManager changes
            if self.log_manager:
                self.log_manager.__exit__(None, None, None)
                
            # Save Workbook Properties
            self.property_manager.apply_changes(write_file_path)
        except Exception as err:
            raise Exception(f"Error occured while attempting to save Workbook data: {err}")