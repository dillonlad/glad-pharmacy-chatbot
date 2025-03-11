import boto3
import base64
import os
from pydantic_settings import BaseSettings

class KMSSettings(BaseSettings):

    class Config:
        env_prefix = "kms_"
        case_sensitive = False

    key_id: str


class KMSClient:
    """
    Handle encyrption and decryption of data using specific AWS KMS key.
    """

    def __init__(self):
        self._kms_client = boto3.client("kms", region_name=os.getenv("AWS_REGION"))
        self._settings = KMSSettings()

    def encrypt_message(self, message):
        """
        Encrypts a message using KMS key
        :param message: string.
        """

        response = self._kms_client.encrypt(
            KeyId=self._settings.key_id,
            Plaintext=message.encode("utf-8")
        )
        return base64.b64encode(response["CiphertextBlob"]).decode("utf-8")

    def decrypt_message(self, encrypted_message):
        """
        Decrypts a message using KMS key.
        :param encrypted_message: bytes.
        """
        
        response = self._kms_client.decrypt(
            CiphertextBlob=base64.b64decode(encrypted_message)
        )
        return response["Plaintext"].decode("utf-8")

    
