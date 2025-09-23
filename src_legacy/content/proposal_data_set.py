from modules.column_manager import ColumnManager

proposal_data_set_config = {
    "file_path": "C:/Users/reyhe/Downloads/SP_Proposals_2025_Apr_22_Data Set 1.xlsx",
    "sheets": {
        "SP_Proposals_2025_Apr_22_Data S": {
            "sheet_identifier": ColumnManager("Proposal Legacy Number")
                .set_property("alias", "proposalLegacyNumber")
                .set_property("sheet", "Proposal - Template"),
            "properties": [
                ColumnManager("Status")
                    .set_property("sheet", "Proposal - Template")
                    .set_property("alias", "status"),
                ColumnManager("Instrument Type")
                    .set_property("sheet", "Proposal - Template")
                    .set_property("alias", "Instrument Type"),
                ColumnManager("Sponsor Primary Code")
                    .set_property("sheet", "Proposal - Template")
                    .set_property("alias", "Sponsor"),
                ColumnManager("Prime Sponsor Primary Code")
                    .set_property("sheet", "Proposal - Template")
                    .set_property("alias", "Prime Sponsor"),
                ColumnManager("Project Title")
                    .set_property("sheet", "Proposal - Template")
                    .set_property("alias", "Title"),
                ColumnManager("Activity Type")
                    .set_property("sheet", "Proposal - Template")
                    .set_property("alias", "Activity Type"),
                ColumnManager("John Jay Centers")
                    .set_property("sheet", "Proposal - Template")
                    .set_property("alias", "John Jay Centers"),
                ColumnManager("Admin Unit Primary Code")
                    .set_property("sheet", "Proposal - Template")
                    .set_property("alias", "Admin Unit")
            ]
        }
    }
}