import json
import requests
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer
from pydantic_settings import BaseSettings
import jwt
from jwt.algorithms import RSAAlgorithm
import boto3

from cognito_user import CognitoUser
from wp_db_handler import DBHandler

# Cognito Configuration
class CognitoSettings(BaseSettings):

    class Config:
        env_prefix = "cognito_"
        case_sensitive = False

    userpool_id: str
    region: str
    app_client_id: str
    algorithms: list[str] = ["RS256"]

security = HTTPBearer()

class CognitoClient:

    def __init__(self):
        self._settings = CognitoSettings()
        self._client = boto3.client("cognito-idp", region_name=self._settings.region)

    @property
    def public_keys(self):
        url = f"https://cognito-idp.{self._settings.region}.amazonaws.com/{self._settings.userpool_id}/.well-known/jwks.json"
        response = requests.get(url)
        return {key["kid"]: key for key in response.json()["keys"]}
    
    @property
    def token_settings(self):
        return {
            "algorithms":self._settings.algorithms,
            "audience":self._settings.app_client_id,
            "issuer":f"https://cognito-idp.{self._settings.region}.amazonaws.com/{self._settings.userpool_id}",
        }
    
    def admin_get_user(self, email):
        return self._client.admin_get_user(UserPoolId=self._settings.userpool_id, Username=email)

    def admin_list_groups_for_user(self, email):
        return self._client.admin_list_groups_for_user(UserPoolId=self._settings.userpool_id, Username=email)
    
    def list_users_in_group(self, group_name):
        print(group_name)
        try:
            return self._client.list_users_in_group(
                UserPoolId=self._settings.userpool_id,
                GroupName=group_name,
                Limit=50,
            )
        except self._client.exceptions.InternalErrorException as e:
            print(e.response)
            return {}
        
    def update_user_attributes(self, username, new_attrs):

        self._client.admin_update_user_attributes(
            UserPoolId=self._settings.userpool_id,
            Username=username,
            UserAttributes=new_attrs
        )

# Function to Verify JWT Token
def verify_token(
        token: str = Security(security), 
        db_handler: DBHandler = Depends(DBHandler.get_session),
    ):

    cognito_client = CognitoClient()
    try:
        headers = jwt.get_unverified_header(token.credentials)
        key = cognito_client.public_keys.get(headers["kid"])

        if not key:
            raise HTTPException(status_code=401, detail="Invalid token")

        decoded_token = jwt.decode(
            token.credentials,
            RSAAlgorithm.from_jwk(json.dumps(key)),
            **cognito_client.token_settings,
        )

        email = decoded_token.get("email")
        sub = decoded_token.get("sub")

        # Check if the user is disabled
        response = cognito_client.admin_get_user(email)
        if response["Enabled"] == False:
            raise HTTPException(status_code=403, detail="User is disabled")

        user_attr = response.get("UserAttributes", [])
        user_email = next((_attr["Value"] for _attr in user_attr if _attr["Name"] == "email"), None)
        user_name = next((_attr["Value"] for _attr in user_attr if _attr["Name"] == "name"), None)

        user_groups_response = cognito_client.admin_list_groups_for_user(email)
        groups = user_groups_response.get("Groups", [])
        is_admin = False
        user_group_names = []
        for group in groups:
            if group["GroupName"] == "glad_admin":
                is_admin = True
            else:
                user_group_names.append(group["GroupName"])

        return CognitoUser(sub, user_email, user_name, is_admin, user_group_names, db_handler, cognito_client)

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
