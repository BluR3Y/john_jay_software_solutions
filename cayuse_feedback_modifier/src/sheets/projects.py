import datetime
import pandas as pd

from classes.Process import Process

SHEET_NAME = "Project - Template"

def populate_project_status(self):
    process_name = "Populate Template Status"
    def logic():
        # Call the same process for the Proposals sheet
        # The process for the Project sheet relies on data from said sheet and should be called as a precaution
        self.processes['Proposal - Template'][process_name].logic()
        
        project_sheet_content = self.template_manager.df[SHEET_NAME]
        proposal_sheet_content = self.template_manager.df["Proposal - Template"]

        for document_index, record in project_sheet_content.iterrows():
            record_pln = record['projectLegacyNumber']
            record_search = proposal_sheet_content.loc[proposal_sheet_content['projectLegacyNumber'] == record_pln]
            if not record_search.empty:
                correlating_proposal_record = record_search.iloc[0]
                proposal_record_status = correlating_proposal_record['status']
                if not pd.isna(proposal_record_status):
                    self.template_manager.update_cell(
                        process_name,
                        SHEET_NAME,
                        document_index,
                        "status",
                        proposal_record_status
                    )
                else:
                    self.comment_manager.append_comment(
                        SHEET_NAME,
                        document_index + 1,
                        project_sheet_content.columns.get_loc('status'),
                        f"The record does not have a status assigned to it in the Proposal sheet."
                    )
                proposal_record_oar = correlating_proposal_record['OAR Status']
                if not pd.isna(proposal_record_oar):
                    self.template_manager.update_cell(
                        process_name,
                        SHEET_NAME,
                        document_index,
                        "OAR Status",
                        proposal_record_oar
                    )
                else:
                    self.comment_manager.append_comment(
                        SHEET_NAME,
                        document_index + 1,
                        project_sheet_content.columns.get_loc('OAR Status'),
                        f"The record does not have an OAR Status assigned to it in the Proposal sheet."
                    )
            else:
                self.comment_manager.append_comment(
                    SHEET_NAME,
                    document_index + 1,
                    project_sheet_content.columns.get_loc('projectLegacyNumber'),
                    f"The record with the projectLegacyNumber {record_pln} does not exist in the proposal sheet."
                )

    return Process(
        logic,
        process_name,
        ""
    )