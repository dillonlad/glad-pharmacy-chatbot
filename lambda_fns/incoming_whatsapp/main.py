import json
import boto3
import os
import pymysql
from db_client import get_db_connection
from kms_client import encrypt_message
import traceback
import mimetypes

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
ORIGINATION_PHONE_NUMBER_ID = os.getenv("ORIGINATION_PHONE_NUMBER_ID")

# AWS Clients
social_messaging_client = boto3.client('socialmessaging')
s3_client = boto3.client('s3')


def lambda_handler(event, context):
    """
    AWS Lambda function that handles WhatsApp Business incoming messages and saves them to MySQL RDS.
    """

    sns_message = json.loads(event["Records"][0]["Sns"]["Message"])

    # Parse incoming WhatsApp message
    body = json.loads(sns_message["whatsAppWebhookEntry"])

    # Extract message details
    phone_number = body["changes"][0]["value"]["messages"][0]["from"]
    profile_name = body["changes"][0]["value"]["contacts"][0]["profile"]["name"]
    message = body["changes"][0]["value"]["messages"][0]
    message_type = message.get("type", "text") 

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 1️⃣ Check if the phone number exists in `conversations`
            cursor.execute("SELECT id FROM conversations WHERE phone_number = %s", (phone_number,))
            conversation = cursor.fetchone()

            new_convo = False
            if not conversation:
                print("Adding new conversation.")
                # 2️⃣ If not found, create a new conversation
                cursor.execute(
                    "INSERT INTO conversations (phone_number, profile_name) VALUES (%s, %s)",
                    (phone_number, profile_name)
                )
                connection.commit()
                conversation_id = cursor.lastrowid
                new_convo = True
            else:
                print("Using existing conersation.")
                conversation_id = conversation["id"]

            if message_type == "text":
                # Handle text messages
                print("Message type text")
                message_text = message["text"]["body"]
                # 3️⃣ Encrypt the message
                encrypted_message = encrypt_message(message_text)
                # 4️⃣ Save the message
                cursor.execute(
                    "INSERT INTO messages (conversation_id, message) VALUES (%s, %s)",
                    (conversation_id, encrypted_message)
                )
                connection.commit()
                connection.close()
            
                # 4️⃣ Handle Media Messages (Images, Videos, Audio, Documents)
            elif message_type in ["image", "video", "document", "audio"]:
                
                print(f"Message type {message_type}")
                media_id = message[message_type]["id"]
                file_extension = ""

                # If it's a document, get the filename extension
                if message_type == "document":
                    file_extension = os.path.splitext(message["document"]["filename"])[-1]
                    s3_key = f"whatsapp-media/{message_type}/{media_id}{file_extension}"
                else:
                    s3_key = f"whatsapp-media/{message_type}/"

                # Retrieve media from WhatsApp and store in S3 using AWS End User Messaging Social
                response = social_messaging_client.get_whatsapp_message_media(
                    mediaId=media_id,
                    originationPhoneNumberId=ORIGINATION_PHONE_NUMBER_ID,
                    destinationS3File={
                        'bucketName': S3_BUCKET_NAME,
                        'key': s3_key
                    }
                )

                print(response)

                if message_type != "document":
                    # For other media types, try to get the file extension from the MIME type.
                    mime_type = message[message_type].get("mime_type")
                    if mime_type:
                        # Guess the extension based on the MIME type (returns something like ".jpg")
                        file_extension = mimetypes.guess_extension(mime_type) or ""

                # Construct the S3 URL
                fp = f"{s3_key}{media_id}{file_extension}"

                metadata = json.dumps({
                    "fp": fp
                })

                caption = message.get(message_type, {}).get("caption", "")
                if caption != "":
                    caption = encrypt_message(caption)

                # Save the media URL in the database
                cursor.execute(
                    "INSERT INTO messages (conversation_id, type, message, metadata) VALUES (%s, %s, %s, %s)",
                    (conversation_id, message_type, caption, metadata)
                )

                if new_convo is False:
                    cursor.execute(
                        "UPDATE conversations set `read`=0 where id = %s", (conversation_id)
                    )

                connection.commit()
                
        return {"statusCode": 200, "body": json.dumps({"message": "Message stored successfully"})}

    except Exception as e:
        print(traceback.format_exc())
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
