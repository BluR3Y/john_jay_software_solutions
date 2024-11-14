import os
import pypdf
import pathlib
import math
from methods import utils
from classes.Process import Process

SHEET_NAME = "Attachments - Template"

def verify_entries(self):
    def logic():
        # Request from user the path to the base directory where the attachments are stored
        input_path = input("Input the path of the directory where the attachments are stored: ")
        dir_path = pathlib.Path(input_path)
        if not dir_path.is_dir():
            raise Exception("Invalid directory provided")
        
        # Store the sheet's content
        sheet_content = self.template_manager.df[SHEET_NAME]
        # Loop through every row in the sheet
        for index, row in sheet_content.iterrows():
            # Retrieve the record's filepath
            file_path = row['filePath']
            if not isinstance(file_path, float):
                full_path = os.path.join(dir_path, file_path)
                if not os.path.isfile(full_path):
                    self.comment_manager.append_comment(
                        SHEET_NAME,
                        index + 1,
                        sheet_content.columns.get_loc('filePath'),
                        "File path does not point to an existing file."
                    )
            else:
                self.comment_manager.append_comment(
                    SHEET_NAME,
                    index + 1,
                    sheet_content.columns.get_loc('filePath'),
                    "Record is missing filePath"
                )

    return Process(
        logic,
        "Verify Attachment Existance",
        "The process goes through every attachment record in the Attachment sheet and validates that the 'filePath' for each record represents an existing file in the local machine."
    )

def missing_project_attachments(self):
    process_name = "Retrieve and Populate Missing Grants From Template Attachments"
    def logic():
        award_sheet_name = 'Award - Template'
        proposal_sheet_name = 'Proposal - Template'
        award_sheet_content = self.template_manager.df[award_sheet_name]
        proposal_sheet_content = self.template_manager.df[proposal_sheet_name]
        attachment_sheet_content = self.template_manager.df[SHEET_NAME]

        # dict with keep track of how many attachments each project has in the 'Attachments' sheet
        attachment_counter = dict()
        for index, project in [*award_sheet_content.iterrows(), *proposal_sheet_content.iterrows()]:
            attachment_counter[project['projectLegacyNumber']] = {
                'legacy_number': project['proposalLegacyNumber'],
                'num_attachments': 0
            }
            
        for index, row in attachment_sheet_content.iterrows():
            if row['projectLegacyNumber'] in attachment_counter:
                attachment_counter[row['projectLegacyNumber']]['num_attachments'] += 1
            else:
                self.comment_manager.append_comment(
                    SHEET_NAME,
                    index + 1,
                    attachment_sheet_content.columns.get_loc('projectLegacyNumber'),
                    f"Grant with projectLegacyNumber '{row['projectLegacyNumber']}' does not exist in either the 'Proposal' or 'Award' sheets."
                )

        new_rows = list()
        for key, props in attachment_counter.items():
            if props['num_attachments'] == 0:
                new_rows.append({
                    'projectLegacyNumber': key,
                    'legacyNumber': props['legacy_number']
                })
            elif props['num_attachments'] < 3:
                first_record = attachment_sheet_content.loc[attachment_sheet_content['projectLegacyNumber'] == key].index[0]
                self.comment_manager.append_comment(
                    SHEET_NAME,
                    first_record + 1,
                    attachment_sheet_content.columns.get_loc('projectLegacyNumber'),
                    f"Only {props['num_attachments']} attachment records exist with the projectLegacyNumber {key}."
                )

        if new_rows:
            self.template_manager.df[SHEET_NAME] = self.template_manager.df[SHEET_NAME].__append(new_rows, ignore_index=True)
            self.log_manager.append_logs(SHEET_NAME, process_name, list(new_rows))

    return Process(
        logic,
        process_name,
        "The process goes through every record in the 'Proposal' and 'Award' sheet and determines the grants that are missing from the 'Attachment' sheet."
    )

def populate_project_info(self):
    process_name = "Fill Missing Attachment Columns"
    def logic():
        # Missing Logging functionality
        sheet_logger = dict()
        attachment_sheet_content = self.template_manager.df[SHEET_NAME]
        projects = dict()

        for index, project in attachment_sheet_content.iterrows():
            if (projects.get(project['legacyNumber']) is None):
                projects[project['legacyNumber']] = {
                    'project_legacy_number': project['projectLegacyNumber'],
                    'legacy_number': project['legacyNumber']
                }

        bundles = [{}]
        bundle_max = 40
        for key in projects:
            if (len(bundles[-1]) == bundle_max):
                bundles.append({})
            bundles[-1][key] = projects[key]
        
        populated_projects = dict()
        for bundle in bundles:
            bundle_ids = [key for key, value in bundle.items()]
            query = f"SELECT Primary_PI, RF_Account, Sponsor_1, Sponsor_2, Grant_ID FROM grants WHERE Grant_ID IN ({','.join(['?' for _ in bundle_ids])})"
            db_data = self.db_manager.execute_query(query, bundle_ids)
            populated_projects.update({bundle[entry['Grant_ID']]['project_legacy_number']: entry for entry in db_data})

        for index, row in attachment_sheet_content.iterrows():
            associated_project = populated_projects.get(row['projectLegacyNumber'])
            if (associated_project):
                attachment_sheet_content.loc[index, 'PI_Name'] = associated_project['Primary_PI']
                attachment_sheet_content.loc[index, 'RF_Account'] = associated_project['RF_Account']
                attachment_sheet_content.loc[index, 'Orig_Sponsor'] = associated_project['Sponsor_2']
                attachment_sheet_content.loc[index, 'Sponsor'] = associated_project['Sponsor_1']
            else:
                first_record = attachment_sheet_content.loc[attachment_sheet_content['legacyNumber'] == row['legacyNumber']].index[0]
                self.comment_manager.append_comment(
                    SHEET_NAME,
                    first_record + 1,
                    attachment_sheet_content.columns.get_loc('legacyNumber'),
                    f"Database does not contain any record with {row['legacyNumber']} as the Grant_ID."
                )
        
        if sheet_logger:
            self.log_manager.append_logs(SHEET_NAME, process_name, sheet_logger)
    return Process(
        logic,
        process_name,
        "This process goes through every record in the 'attachments' sheet and populates the PI_NAME, RF_Account, Orig_Sponsor, and Sponsor columns in the sheet with information retrieved from the database."
    )