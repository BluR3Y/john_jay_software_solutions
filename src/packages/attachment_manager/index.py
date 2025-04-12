import boto3
import requests

class AttachmentManager:
    def __init__(self):
        self.client = boto3.client('workdocs', region_name='us-east-1')
        response = self.client.describe_users(OrganizationId='d-90679e3814',Query='reflores@jjay.cuny.edu')
        print(response)
        # LAst Here