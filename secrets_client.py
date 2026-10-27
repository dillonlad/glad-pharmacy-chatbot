import json
import os
import boto3
from pydantic_settings import BaseSettings


class SecretsManagerSettings(BaseSettings):

    class Config:
        env_prefix = "secrets_"
        case_sensitive = False

    # Optional default region if AWS_REGION environment variable isn't set
    region_name: str = "eu-west-2"


class SecretsManagerClient:
    """
    Handle retrieving secrets from AWS Secrets Manager.
    """

    def __init__(self):
        self._settings = SecretsManagerSettings()
        # Fallback to settings region_name if AWS_REGION is not set in the environment
        region = os.getenv("AWS_REGION", self._settings.region_name)
        self._client = boto3.client("secretsmanager", region_name=region)

    def get_secret_value(self, secret_id: str) -> str:
        """
        Retrieves the raw string value of a secret (useful for plain text secrets).
        :param secret_id: string (Name or ARN of the secret).
        """
        response = self._client.get_secret_value(SecretId=secret_id)
        
        # Secrets Manager returns either SecretString or SecretBinary
        if "SecretString" in response:
            return response["SecretString"]
        else:
            return response["SecretBinary"].decode("utf-8")

    def get_secret_dict(self, secret_id: str) -> dict:
        """
        Retrieves a key/value secret stored as a JSON string and parses it into a dictionary.
        :param secret_id: string (Name or ARN of the secret).
        """
        secret_string = self.get_secret_value(secret_id)
        
        try:
            return json.loads(secret_string)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Secret '{secret_id}' is not formatted as a valid JSON dictionary."
            ) from e