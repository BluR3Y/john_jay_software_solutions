import os
import pypdf
from configs.openai_config import client

# Attachment file types: ['.pdf', '.docx', '.xlsx', '.msg', '.xls', '.xlsm', '.doc']
SHEET_NAME = "Attachments - Template"
SHARED_DIR = "F:/Proposals"
ATTACHMENT_TYPES = {
    'Application Package': {
        'synonyms': ['proposal package', 'application', 'submission package'],
        'description': 'It is a document that has every requirement required to apply for a grant'
    },
    'Budget': {
        'synonyms': [],
        'description': 'A sponsor specific budget document'
    },
    'Budget (internal)': {
        'synonyms': ['OAR budget template'],
        'description': 'The most recent budget mockup'
    },
    'Budget Justification': {
        'synonyms': ['budget narrative'],
        'description': ''
    },
    'Other': {
        'synonyms': ['award letter', 'award document', 'contract', 'fully executed agreement'],
        'description': ''
    },
    'Proposal Narrative': {
        'synonyms': ['project narrative', 'proposal', 'project description'],
        'description': 'This type of document is part of the Application Package'
    },
    'Letter of Intent': {
        'synonyms': [],
        'description': 'Use this type sparingly. Use case would be when a document does not resemble a proposal in it\'s entirety but has attributes that might consider it a letter of intent.'
    },
}

def verify_entries(self):
    # Store the sheet's content
    sheet_content = self.df[SHEET_NAME]
    sheet_logger = dict()
    
    # Loop through every row in the sheet
    for index, row in sheet_content.iterrows():

        # Store the path of the file that will be verified
        attachment_path = os.path.join(SHARED_DIR, row['filePath'])
        
        # If the path represents an existing file:
        if os.path.isfile(attachment_path):
            # Experimental Condition
            continue
            try:
                file_content = extract_file_content(attachment_path)
                file_classification = classify_document(file_content)
                if row['attachment type'] != file_classification:
                    sheet_logger[f"{row['legacyNumber']}:attachmentType"] = f"File is detected to have the wrong attachment type. It's ideal type is '{file_classification}'"
            except Exception as err:
                sheet_logger[f"{row['legacyNumber']}:fileExtension"] = err
        else:
            sheet_logger[f"{row['legacyNumber']}:fileExistance"] = f"File does not exist in directory"


    # If no prior logs have been created for the current sheet, initialize the property in the logger's modifications for that sheet
    if SHEET_NAME not in self.logger['modifications']:
        self.logger['modifications'][SHEET_NAME] = sheet_logger
    # Else, add the properties of the sheet to the class logger
    else:
        self.logger['modifications'][SHEET_NAME].update(sheet_logger)

# Helper function to extract text from different file formats
def extract_file_content(file_path):
    file_ext = os.path.splitext(file_path)[1]
    if (file_ext == '.pdf'):
        # Create file reader
        reader = pypdf.PdfReader(file_path)
        
        # Extract the file contents
        file_content = ''
        for page in reader.pages:
            file_content += page.extract_text() + '\n'
        return file_content
    else:
        raise Exception("Script does not support the file's extension type: " + file_ext)
    
# Function to classify the document content using OpenAI
def classify_document(document_content):
    form_types_description = "\n".join([
        f"{form}: {details['description']} (Synonyms: {', '.join(details['synonyms']) if details['synonyms'] else 'None'})"
        for form, details in ATTACHMENT_TYPES.items()
    ])

    prompt = f"""
    Below are different form attachment types with their descriptions and synonyms:

    {form_types_description}

    Based on the content of the document below, determine which attachment type this document is most likely related to. 
    Please return only the form type name without any explanation or additional text.

    Document Content:
    {document_content}
    """

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an assistant helping classify documents."},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content

# Function to account for projects that don't have attachments
def missing_project_attachments(self):
    award_sheet_name = 'Award - Template'
    proposal_sheet_name = 'Proposal - Template'
    award_sheet_content = self.df[award_sheet_name]
    proposal_sheet_content = self.df[proposal_sheet_name]
    attachment_sheet_content = self.df[SHEET_NAME]
    sheet_logger = {
        'no_attachments': [],
        'less_than_three_attachments': []
    }

    project_attachments = dict()
    for index, project in [*award_sheet_content.iterrows(), *proposal_sheet_content.iterrows()]:
        project_attachments[project['projectLegacyNumber']] = {
            'legacy_number': project['proposalLegacyNumber'],
            'num_attachments': 0
        }
        
    for legacyNum in attachment_sheet_content['projectLegacyNumber']:
        project_attachments[legacyNum]['num_attachments'] += 1

    new_rows = list()
    for key, prop in project_attachments.items():
        if (prop['num_attachments'] == 0):
            sheet_logger['no_attachments'].append(key)
            new_rows.append({
                'projectLegacyNumber': key,
                'legacyNumber': prop['legacy_number']
            })
        elif (prop['num_attachments'] < 3):
            sheet_logger['less_than_three_attachments'].append(key)
    
    self.df[SHEET_NAME] = self.df[SHEET_NAME]._append(new_rows, ignore_index=True)

    # If no prior logs have been created for the current sheet, initialize the property in the logger's modifications for that sheet
    if SHEET_NAME not in self.logger['modifications']:
        self.logger['modifications'][SHEET_NAME] = sheet_logger
    # Else, add the properties of the sheet to the class logger
    else:
        self.logger['modifications'][SHEET_NAME].update(sheet_logger)

# Function to retrieve information related to the project from the database
def retrieve_project_info(self):
    sheet_logger = dict()
    attachment_sheet_content = self.df[SHEET_NAME]
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

    sheet_logger['attachment_data'] = dict()
    for bundle in bundles:
        bundle_ids = [key for key, value in bundle.items()]
        query = f"SELECT Primary_PI, RF_Account, Sponsor_1, Sponsor_2, Grant_ID FROM grants WHERE Grant_ID IN ({','.join(['?' for _ in bundle_ids])})"
        db_data = self.execute_query(query, bundle_ids)
        db_data_dict = {bundle[entry['Grant_ID']]['project_legacy_number']: entry for entry in db_data}
        
        sheet_logger['attachment_data'].update(db_data_dict)
        
    # If no prior logs have been created for the current sheet, initialize the property in the logger's modifications for that sheet
    if SHEET_NAME not in self.logger['modifications']:
        self.logger['modifications'][SHEET_NAME] = sheet_logger
    # Else, add the properties of the sheet to the class logger
    else:
        self.logger['modifications'][SHEET_NAME].update(sheet_logger)