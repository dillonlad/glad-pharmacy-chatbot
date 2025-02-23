import boto3
import base64
import os

# AWS KMS Client
kms_client = boto3.client("kms", region_name=os.getenv("AWS_REGION"))

KMS_KEY_ID = os.getenv("KMS_KEY_ID")

def encrypt_message(message):
    print("encrypting", message)
    response = kms_client.encrypt(
        KeyId=KMS_KEY_ID,
        Plaintext=message.encode("utf-8")
    )
    return base64.b64encode(response["CiphertextBlob"]).decode("utf-8")

def decrypt_message(encrypted_message):
    response = kms_client.decrypt(
        CiphertextBlob=base64.b64decode(encrypted_message)
    )
    return response["Plaintext"].decode("utf-8")
