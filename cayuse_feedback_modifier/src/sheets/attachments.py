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
            try:
                file_content = extract_file_content(attachment_path)
                file_classification = classify_document(file_content)
                if row['attachment type'] != file_classification:
                    sheet_logger[f"{row['legacyNumber']}:attachmentType"] = f"File is detected to have the wrong attachment type. It's ideal type is '{file_classification}'"
            except Exception as err:
                sheet_logger[f"{row['legacyNumber']}:fileExtension"] = err


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