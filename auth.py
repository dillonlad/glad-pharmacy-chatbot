import json
import requests
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer
import jwt
from jwt.algorithms import RSAAlgorithm
import boto3

# Cognito Configuration
COGNITO_USERPOOL_ID = "eu-west-2_kvNlJXgmz"
COGNITO_REGION = "eu-west-2"
COGNITO_APP_CLIENT_ID = "gfcild4r1f3nb7b1mp13vtfql"

client = boto3.client("cognito-idp", region_name=COGNITO_REGION)

security = HTTPBearer()

# Fetch Cognito Public Keys
def get_cognito_public_keys():
    url = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USERPOOL_ID}/.well-known/jwks.json"
    response = requests.get(url)
    return {key["kid"]: key for key in response.json()["keys"]}

public_keys = get_cognito_public_keys()

# Function to Verify JWT Token
def verify_token(token: str = Security(security)):
    try:
        headers = jwt.get_unverified_header(token.credentials)
        key = public_keys.get(headers["kid"])

        if not key:
            raise HTTPException(status_code=401, detail="Invalid token")

        decoded_token = jwt.decode(
            token.credentials,
            RSAAlgorithm.from_jwk(json.dumps(key)),
            algorithms=["RS256"],
            audience=COGNITO_APP_CLIENT_ID,
            issuer=f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USERPOOL_ID}",
        )

        email = decoded_token.get("email")
        print(email, decoded_token)

        # ✅ Check if the user is disabled
        response = client.admin_get_user(UserPoolId=COGNITO_USERPOOL_ID, Username=email)
        print(response)
        if response["Enabled"] == False:
            raise HTTPException(status_code=403, detail="User is disabled")

        return decoded_token  # Contains user info like email, sub (user ID), etc.

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
