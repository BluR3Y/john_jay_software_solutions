import pandas as pd

class SheetManager:
    populating_methods = []
    
    def __init__(self, sheet_name, columns, append_fn):
        self.sheet_name = sheet_name
        self.df = pd.DataFrame(columns)
        self.append_fn = append_fn
        
    def append_method(self, ref):
        self.populating_methods.append(ref)
        
    def append_grant(self, grant):
        row_data = self.append_fn(grant)
        # New row as a DataFrame
        new_row = pd.DataFrame(row_data)
        # Append using pd.concat
        self.df = pd.concat([self.df, new_row], ignore_index=True)