import os
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from packages.workbook_manager import WorkbookManager
from packages.database_manager import DatabaseManager
from packages.content_manager import ContentManager

from .sheets.projects import projects_sheet_append
from .sheets.members import members_sheet_append
from .sheets.proposals import proposals_sheet_append
from .sheets.awards import awards_sheet_append

class MigrationManager:
    config_dir_path = Path(__file__).resolve().parent / 'configs'

    def __init__(self, db_path: str, reference_path: str):
        # Initialize an instance of the WorkbookManager class
        self.db_manager = DatabaseManager(db_path,"Migration Manager").__enter__()

        # Initialize an instance of the WorkbookManager class for the reference file
        self.reference_wb_manager = WorkbookManager(reference_path).__enter__()

        # Initialize an instance of the WorkbookManager class for the generated data
        self.generated_wb_manager = WorkbookManager().__enter__()

        # Initialize an instance of the ContentManager class for grant attachment files
        self.attachment_manager = ContentManager

    def __enter__(self):
        current_date = datetime.now()
        formatted_date = current_date.strftime('%d_%m_%Y')
        self.generated_wb_manager.set_write_path(os.path.join(os.getenv("SAVE_PATH"), f"generated_data_{formatted_date}.xlsx"))

        self._retrieve_wb_config()
        self._retrieve_internal_orgs()
        self._retrieve_external_orgs()
        self._retrieve_centers()
        self._retrieve_people()
        self._retrieve_associations()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.generated_wb_manager._save_data()
        # self.attachment_manager.__exit__(exc_type, exc_value, traceback)

    def _retrieve_wb_config(self):        
        # Retrieve template Sheets/Columns
        with open(self.config_dir_path / 'gen_wb_layout.json', encoding='utf-8') as f:
            gen_sheets = json.load(f)
            for sheet_name, sheet_columns in gen_sheets.items():
                self.generated_wb_manager.create_sheet(sheet_name, sheet_columns)

    # def _retrieve_people(self):
    #     people = {}
    #     people_sheet_manager = self.reference_wb_manager["Data - People"]

    #     for index, row in people_sheet_manager.get_df(format=True).iterrows():
    #         if index == 0:
    #             continue

    #         f_name, m_name, l_name, emp_id, username = row

    #         # Normalize and clean name data
    #         first_name = f_name.strip().capitalize() if f_name else None
    #         middle_name = m_name.strip().capitalize() if m_name and len(m_name) else None
    #         last_name = re.sub(r"\s*\(\d{8}\)$", "", l_name).strip().capitalize()
    #         email = str(username).strip() if username else None

    #         # Retrieve existing or create new
    #         person = people.get(emp_id, {
    #             "name": {"first": None, "middle": None, "last": None},
    #             "empl_id": emp_id,
    #             "email": None
    #         })
            
    #         # Fill in missing details
    #         person["name"]["first"] = person["name"]["first"] or first_name
    #         person["name"]["middle"] = person["name"]["middle"] or middle_name
    #         person["name"]["last"] = person["name"]["last"] or last_name
    #         person["empl_id"] = person["empl_id"] or emp_id
    #         person["email"] = person["email"] or email
            
    #         # Save back to the dictionary
    #         people[emp_id] = person

    #     self.PEOPLE = people
    def _retrieve_people(self):
        with open(self.config_dir_path / 'john_jay_investigators.json', 'r', encoding='utf-8') as f:
            self.INVESTIGATORS = json.load(f)

        def format_name(first: str, middle: str, last: str) -> str:
            return f"{last}, {f"{first} {middle}" if middle else first}"

        self.FORMAT_INVESTIGATORS = {format_name(*person.get('name').values()): empl for empl, person in self.INVESTIGATORS.items()}

    def _retrieve_internal_orgs(self):
        with open(self.config_dir_path / 'john_jay_org_units.json', 'r', encoding='utf-8') as f:
            self.INTERNAL_ORGS = json.load(f)

    def _retrieve_external_orgs(self):
        with open(self.config_dir_path / 'john_jay_external_orgs.json', 'r', encoding='utf-8') as f:
            self.EXTERNAL_ORGS = json.load(f)
    
    def _retrieve_centers(self):
        with open(self.config_dir_path / 'john_jay_centers.json', 'r', encoding='utf-8') as f:
            self.CENTERS = json.load(f)

    def _retrieve_associations(self):
        with open(self.config_dir_path / 'john_jay_associations.json', 'r', encoding='utf-8') as f:
            association_data = json.load(f)
        
        self.INSTRUMENT_TYPES = association_data.get('instrument_types')
        self.ACTIVITY_TYPES = association_data.get('activity_types')
        self.DISCIPLINES = association_data.get('disciplines')

    @staticmethod
    def determine_best_match(ref_sol, gen_sol) -> tuple:
        if ref_sol and gen_sol:
            return (ref_sol, f"Referenced value differs from generated value: {gen_sol}" if ref_sol != gen_sol else None)
        elif ref_sol:
            return (ref_sol, "Status was determined using reference workbook.")
        elif gen_sol:
            return (gen_sol, None)

MigrationManager.projects_sheet_append = projects_sheet_append
MigrationManager.members_sheet_append = members_sheet_append
MigrationManager.proposals_sheet_append = proposals_sheet_append
MigrationManager.awards_sheet_append = awards_sheet_append