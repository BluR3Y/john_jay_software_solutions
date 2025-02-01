import os
import pandas as pd
import openpyxl

from packages.database_manager import DatabaseManager

class ReportGenerator:
    process_name = "Report Generator"
    generated_reports = {}
    
    def __init__(self, save_path):
        self.save_path = save_path
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        generated_reports = self.generated_reports
        if generated_reports:
            save_location = os.path.join(self.save_path, "generated_report.xlsx")
            meta_data_sheet_name = "report_meta_data"
            # Use ExcelWriter to write multiple sheets into an Excel file
            with pd.ExcelWriter(save_location) as writer:
                meta_data_columns = ['sheet_name', 'table', 'record_identifier']
                report_meta_data = []
                for sheet_name, sheet_info in generated_reports.items():
                    df_sheet = pd.DataFrame(sheet_info["report_data"])
                    df_sheet.to_excel(writer, sheet_name=sheet_name, index=False)
                    report_meta_data.append([sheet_name, sheet_info['table'], sheet_info['record_identifier']])
                
                # Create MetaData DataFrame
                meta_data_frame = pd.DataFrame(report_meta_data, columns=meta_data_columns)
                meta_data_frame.to_excel(writer, sheet_name=meta_data_sheet_name, index=False)
            
            # Load the report workbook
            report_workbook = openpyxl.load_workbook(save_location)
            # Set the state of the MetaData sheet as hidden
            report_workbook[meta_data_sheet_name].sheet_state = "hidden"
            # Save the state change made to the workbook
            report_workbook.save(save_location)
            
    def append_report(self, report_name: str, table: str, record_identifier: str, report_data: list[dict]):
        self.generated_reports[report_name] = {
            "table": table,
            "record_identifier": record_identifier,
            "report_data": report_data
        }
            
    # def parse_query_conditions(self, condition_str, valid_columns):
    #     # Define valid operators and keywords
    #     OPERATORS = ['=', '<>', '!=', '<', '<=', '>', '>=', 'LIKE', 'NOT LIKE', 'REGEXP', 'NOT REGEXP', 'IN', 'NOT IN', 'IS', 'IS NOT', 'BETWEEN']
    #     LOGICAL_OPERATORS = ['AND', 'OR']
    #     NULL_VALUES = ['NULL', 'Null']
    #     PARENTHESIS = r"\((.*?)\)"
        
    #     # Helper function to check if an operator is valid
    #     def is_valid_operator(operator):
    #         return operator in OPERATORS

    #     # Helper function to split condition into left and right parts
    #     def split_condition(condition):
    #         for operator in OPERATORS:
    #             if operator in condition:
    #                 left, right = condition.split(operator, 1)
    #                 if is_valid_operator(operator):  # Only proceed if the operator is valid
    #                     return left.strip(), operator, right.strip()
    #         return None, None, None

    #     # Function to parse the condition recursively
    #     def parse_sub_condition(sub_condition):
    #         # If condition is grouped in parentheses, extract and recurse
    #         if sub_condition.startswith('(') and sub_condition.endswith(')'):
    #             sub_condition = sub_condition[1:-1]
    #             return self.parse_query_conditions(sub_condition, valid_columns)

    #         # Look for logical operators AND/OR
    #         for logical_operator in LOGICAL_OPERATORS:
    #             parts = sub_condition.split(logical_operator, 1)
    #             if len(parts) > 1:
    #                 left = parse_sub_condition(parts[0].strip())
    #                 right = parse_sub_condition(parts[1].strip())
    #                 return {logical_operator: [left, right]}

    #         # Split based on operators and handle each operator type
    #         left, operator, right = split_condition(sub_condition)
    #         if left and operator and right:
    #             left = left.strip()
    #             right = right.strip()

    #             # Check for NULL condition
    #             if any(null_val in right for null_val in NULL_VALUES):
    #                 return {left: {'operator': 'IS', 'value': right}}

    #             # Handle IN, NOT IN
    #             if operator in ['IN', 'NOT IN']:
    #                 values = right[1:-1].split(',')
    #                 return {left: {'operator': operator, 'value': [v.strip() for v in values]}}

    #             # Handle LIKE, NOT LIKE, REGEXP, NOT REGEXP
    #             if operator in ['LIKE', 'NOT LIKE', 'REGEXP', 'NOT REGEXP']:
    #                 return {left: {'operator': operator, 'value': right}}

    #             # Handle BETWEEN
    #             if operator == 'BETWEEN':
    #                 lower, upper = right.split('AND')
    #                 return {left: {'operator': operator, 'value': (lower.strip(), upper.strip())}}

    #             # Otherwise return normal condition
    #             return {left: {'operator': operator, 'value': right}}

    #         return {}

    #     # Main function logic
    #     condition_str = condition_str.strip()

    #     # Start parsing
    #     return parse_sub_condition(condition_str)