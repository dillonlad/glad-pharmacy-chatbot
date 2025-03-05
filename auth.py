import json
import requests
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer
from pydantic_settings import BaseSettings
import jwt
from jwt.algorithms import RSAAlgorithm
import boto3

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

cognito_settings = CognitoSettings()
client = boto3.client("cognito-idp", region_name=cognito_settings.region)

security = HTTPBearer()

# Fetch Cognito Public Keys
def get_cognito_public_keys():
    url = f"https://cognito-idp.{cognito_settings.region}.amazonaws.com/{cognito_settings.userpool_id}/.well-known/jwks.json"
    response = requests.get(url)
    return {key["kid"]: key for key in response.json()["keys"]}

public_keys = get_cognito_public_keys()

# Function to Verify JWT Token
def verify_token(
        token: str = Security(security), 
        db_handler: DBHandler = Depends(DBHandler.get_session),
    ):
    try:
        headers = jwt.get_unverified_header(token.credentials)
        key = public_keys.get(headers["kid"])

        if not key:
            raise HTTPException(status_code=401, detail="Invalid token")

        decoded_token = jwt.decode(
            token.credentials,
            RSAAlgorithm.from_jwk(json.dumps(key)),
            algorithms=cognito_settings.algorithms,
            audience=cognito_settings.app_client_id,
            issuer=f"https://cognito-idp.{cognito_settings.region}.amazonaws.com/{cognito_settings.userpool_id}",
        )

        email = decoded_token.get("email")

        # ✅ Check if the user is disabled
        response = client.admin_get_user(UserPoolId=cognito_settings.userpool_id, Username=email)
        if response["Enabled"] == False:
            raise HTTPException(status_code=403, detail="User is disabled")

        return db_handler

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
