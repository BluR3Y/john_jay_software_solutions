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
        
        project_sheet_content = self.df[SHEET_NAME]
        proposal_sheet_content = self.df["Proposal - Template"]

        for document_index, record in project_sheet_content.iterrows():
            record_pln = record['projectLegacyNumber']
            correlating_proposal_record = proposal_sheet_content.loc[proposal_sheet_content['projectLegacyNumber'] == record_pln].iloc[0]
            if not correlating_proposal_record.empty:
                proposal_record_status = correlating_proposal_record['status']
                if not pd.isna(proposal_record_status):
                    proposal_sheet_content.loc[document_index, 'status'] = proposal_record_status
                else:
                    self.comment_manager.append_comment(
                        SHEET_NAME,
                        document_index + 1,
                        project_sheet_content.columns.get_loc('status'),
                        f"The record does not have a status assigned to it in the Proposal sheet."
                    )
            else:
                print(record_pln)
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