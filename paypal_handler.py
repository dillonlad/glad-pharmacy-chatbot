from pydantic_settings import BaseSettings
from fastapi import HTTPException
import httpx

class PayPalConfig(BaseSettings):
    
    class Config:
        env_prefix = "paypal_"
        case_sensitive = False

    client_id: str
    live_secret: str
    url: str = "https://api-m.paypal.com"
    auth_uri: str = "/v1/oauth2/token"
    auth_headers: dict[str, str] = {"Accept": "application/json", "Accept-Language": "en_US"}
    auth_data: dict[str, str] = {"grant_type": "client_credentials"}

class PayPalHandler:

    def __init__(self):
        self._settings = PayPalConfig()
        self._auth = (self._settings.client_id, self._settings.live_secret)
        self._bearer_token = None
        self._client = None

    def start_session(self):
        with httpx.Client(
            base_url=self._settings.url, 
            auth=self._auth,
            headers=self._settings.auth_headers
        ) as auth_client:
            auth_response = auth_client.post(self._settings.auth_uri, data=self._settings.auth_data)

        if auth_response.status_code != 200:
            print(auth_response)
            raise HTTPException(status_code=500, detail="Failed to obtain PayPal access token")
        
        self._bearer_token = auth_response.json().get("access_token")
        headers = {
            **self._settings.auth_headers,
            "Authorization": f"Bearer {self._bearer_token}"
        }
        self._client = httpx.Client(base_url=self._settings.url, headers=headers)

    def void_auth(self, auth_id):

        void_response = self._client.post(
            f"/v2/payments/authorizations/{auth_id}/void",
            headers={
                "Content-Type": "application/json"
            }
        )
    
        if void_response.status_code == 204:
            return {"message": "PayPal authorization voided successfully."}
        else:
            return HTTPException(status_code=void_response.status_code, detail=void_response.json())
        
    def capture_auth(self, auth_id):

        void_response = self._client.post(
            f"/v2/payments/authorizations/{auth_id}/capture",
            headers={
                "Content-Type": "application/json"
            }
        )
    
        if void_response.status_code == 204:
            return {"message": "PayPal authorization captured successfully."}
        else:
            return HTTPException(status_code=void_response.status_code, detail=void_response.json())
        
    def close_session(self):
        self._client.close()