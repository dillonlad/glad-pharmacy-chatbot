from pydantic_settings import BaseSettings
import boto3
import json
from cognito_user import CognitoUser
from auth import CognitoClient
from logging import getLogger
from enum import Enum

RECIPIENT = "recipient@example.com"
SUBJECT = "Hello from Amazon SES via Python"
CHARSET = "UTF-8"

class SESTemplates(Enum):

    ANNUAL_LEAVE_REQUEST = "AnnualLeaveRequest"
    ANNUAL_LEAVE_APPROVED = "AnnualLeaveApproved"
    ANNUAL_LEAVE_REJECTED = "AnnualLeaveRejected"

class SESSettings(BaseSettings):

    class Config:
        env_prefix = "ses_"
        case_sensitive = False

    sender: str = "dashboard@gladpharmacy.com"
    dashboard_url: str = "dashboard.gladpharmacy.co.uk"

class SESClient:

    def __init__(self):
        self._settings = SESSettings()
        self._client = boto3.client("ses")
        self._logger = getLogger("fastapi")

    def send_email(
            self, 
            template_name: SESTemplates, 
            template_data: dict,
            recipients: list[str]
        ):

        template_data["portal_link"] = self._settings.dashboard_url
        response = self._client.send_templated_email(
            Source=f"Glad Pharmacy <{self._settings.sender}>",
            Destination={
                'ToAddresses': recipients,
            },
            Template=template_name.value,
            TemplateData=json.dumps(template_data)
        )
        return response

    def send_managers_email(self, user: CognitoUser, template_name: SESTemplates, template_data: dict):

        user_managers = user.get_users_manager()
        recipients = [manager["email"] for manager in user_managers if manager["email"] not in [None, ""]]
        if len(recipients) == 0:
            return
        
        self.send_email(template_name, template_data, recipients)

        return
        
    def send_user_email(
            self, 
            cognito_client: CognitoClient,
            user_sub: str, 
            template_name: SESTemplates, 
            template_data: dict,
        ):
        
        matching_user = cognito_client.get_user_from_sub(user_sub)
        if matching_user is None:
            return None
        
        user_attr = matching_user.get("Attributes", [])
        user_name = next((_attr["Value"] for _attr in user_attr if _attr["Name"] == "name"), None)
        user_email = next((_attr["Value"] for _attr in user_attr if _attr["Name"] == "email"), None)
        if user_email is None:
            return None
        
        template_data["staff_name"] = user_name
        
        self.send_email(
            template_name,
            template_data,
            [user_email],
        )
        

