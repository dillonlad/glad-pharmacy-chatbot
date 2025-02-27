from pydantic_settings import BaseSettings
import boto3
import json
import os
import traceback
import mimetypes
from datetime import datetime
from fastapi import HTTPException
from kms_client import KMSClient
from wp_db_handler import DBHandler
from logging import getLogger


class WhatsAppSettings(BaseSettings):

    class Config:
        env_prefix = "whatsapp_"
        case_sensitive = False

    phone_number_id: str
    meta_api_version: str = "v20.0"
    s3_bucket_name: str = "glad-whatsapp"


class WhatsAppClient:

    def __init__(self, db_handler: DBHandler):
        
        self._settings = WhatsAppSettings()
        self._kms_client = KMSClient()
        self._db_handler = db_handler
        self._socialmessaging_client = boto3.client('socialmessaging')
        self._logger = getLogger("fastapi")

    def send_message(
            self, 
            conversation_id,
            message_type, 
            message,
        ):

        previous_messages = self.get_conversation(conversation_id)

        conversation = self._db_handler.fetchone(
            "SELECT id, phone_number from conversations where id = {}".format(conversation_id)
        )
        recipient = conversation["phone_number"]

        # Construct the message payload
        message_payload = {
            "messaging_product": "whatsapp",
            "to": f"+{recipient}",
            "type": message_type,
            "text": {"body": message}
        }
        
        # Encode the message payload to base64
        encoded_message = json.dumps(message_payload).encode()
        # Send the message using AWS End User Messaging Social
        response = self._socialmessaging_client.send_whatsapp_message(
            message=encoded_message,
            originationPhoneNumberId=self._settings.phone_number_id,
            metaApiVersion=self._settings.meta_api_version
        )

        if response.get("ResponseMetadata", {}).get("HTTPStatusCode", None) == 200 and response.get("messageId", None) is not None:

            encrypted_message = self._kms_client.encrypt_message(message)

            sql = "INSERT INTO messages (conversation_id, message, is_me) \
                VALUES (%s, '%s', 1)" % (conversation_id, encrypted_message) if message_type == "text" else "INSERT \
                    INTO messages (conversation_id, message, is_me) VALUES (%s, '%s', 1)" % (conversation_id, encrypted_message)
            self._db_handler.execute(sql, commit=True)

        else:
            raise HTTPException(status_code=500, detail="Failed to send WhatsApp message.")
        
        previous_messages["messages"].append({"id": -1, "message": message, "type": message_type, "isMe": True})
        return previous_messages
    
    def get_channels(self):
        
        sql = """
                select conversations.id, conversations.profile_name as `title`, top_message.created as `date`, case when top_message.message is not null and top_message.message != '' then top_message.message when top_message.metadata is not null then 'Multimedia' else 'No Messages' end as `subtitle`, conversations.read
                from conversations
                left outer join (
                SELECT m1.conversation_id, m1.message, m1.metadata, m1.created
                FROM messages m1
                JOIN (
                SELECT conversation_id, MAX(created) AS latest
                FROM messages
                GROUP BY conversation_id
                ) m2 ON m1.conversation_id = m2.conversation_id 
                AND m1.created = m2.latest
                ORDER BY m1.created DESC
                ) top_message on conversations.id=top_message.conversation_id
                order by conversations.read asc, top_message.created desc
              """

        channels = self._db_handler.fetchall(sql)
        decrypted_channels = []
        current_date = datetime.now().date()
        for _channel in channels:
            channel = _channel
            if _channel["subtitle"] not in ["Multimedia", "No Messages", ""]:
                channel["subtitle"] = self._kms_client.decrypt_message(_channel["subtitle"])
            channel["unread"] = True if not _channel["read"] else False
            decrypted_channels.append(channel)
            if isinstance(_channel["date"], datetime):
                if _channel["date"].date() == current_date:
                    channel["date"] = _channel["date"].time()
                else:
                    channel["date"] = _channel["date"].date()

        return {"channels": channels}

    def get_conversation(self, id, mark_as_read=True):
        """
        Get all of the messages for an individual conversation.
        """
        
        sql = """
                SELECT messages.id, messages.type, messages.message, messages.metadata, messages.is_me 
                from conversations
                inner join messages on conversations.id=messages.conversation_id 
                where conversations.id = {}
                order by messages.created asc;
              """.format(id)
        messages = self._db_handler.fetchall(sql)
        formatted_messages = []
        for message in messages:
            _message = message
            if message["message"] != "":
                _message["message"] = self._kms_client.decrypt_message(message["message"])
            if message["type"] != "text" and message["metadata"]:
                attachment_url = json.loads(message["metadata"]).get("media_url", "")
                _message["message"] += f"\nAttachment: {attachment_url}"
            _message["isMe"] = message["is_me"]
            formatted_messages.append(_message)

        if mark_as_read is True:
            update_sql = """update conversations set `read`=1 where id = {}""".format(id)
            self._db_handler.execute(update_sql, commit=True)

        return {"messages": formatted_messages}
    
    def get_unread_conversations(self):
        """
        Get the number of unread messages.
        """

        sql = "SELECT COUNT(id) AS unread_messages FROM conversations where `read`=0"
        _count = self._db_handler.fetchone(sql)
        return _count["unread_messages"]
    
    def process_incoming_message(self, whatsapp_webhook_entry, message_id):

        if "messages" not in whatsapp_webhook_entry["changes"][0]["value"]:
            self._logger.info("Other WhatsApp queued message")
            return
        
        # Extract message details
        phone_number = whatsapp_webhook_entry["changes"][0]["value"]["messages"][0]["from"]
        profile_name = whatsapp_webhook_entry["changes"][0]["value"]["contacts"][0]["profile"]["name"]
        message = whatsapp_webhook_entry["changes"][0]["value"]["messages"][0]
        message_type = message.get("type", "text") 

        try:

            with self._db_handler._cursor as cursor:
                # Check if this is a repeated SQS message
                cursor.execute("select id from messages where sns_message_id = %s", (message_id,))
                existing_message = cursor.fetchone()

                if existing_message is not None:
                    return

                # 1️⃣ Check if the phone number exists in `conversations`
                cursor.execute("SELECT id FROM conversations WHERE phone_number = %s", (phone_number,))
                conversation = cursor.fetchone()

                new_convo = False
                if not conversation:
                    self._logger.debug("Adding new conversation.")
                    # 2️⃣ If not found, create a new conversation
                    cursor.execute(
                        "INSERT INTO conversations (phone_number, profile_name) VALUES (%s, %s)",
                        (phone_number, profile_name)
                    )
                    self._db_handler._conn.commit()
                    conversation_id = cursor.lastrowid
                    new_convo = True
                else:
                    self._logger.debug("Using existing conersation.")
                    conversation_id = conversation["id"]

                if message_type == "text":
                    # Handle text messages
                    self._logger.debug("Message type text")
                    message_text = message["text"]["body"]
                    # 3️⃣ Encrypt the message
                    encrypted_message = self._kms_client.encrypt_message(message_text)
                    # 4️⃣ Save the message
                    cursor.execute(
                        "INSERT INTO messages (conversation_id, message, sns_message_id) VALUES (%s, %s, %s)",
                        (conversation_id, encrypted_message, message_id)
                    )
                    self._db_handler._conn.commit()
                    self._db_handler._conn.close()
                
                    # 4️⃣ Handle Media Messages (Images, Videos, Audio, Documents)
                elif message_type in ["image", "video", "document", "audio"]:
                    
                    self._logger.debug(f"Message type {message_type}")
                    media_id = message[message_type]["id"]
                    file_extension = ""

                    # If it's a document, get the filename extension
                    if message_type == "document":
                        file_extension = os.path.splitext(message["document"]["filename"])[-1]
                        s3_key = f"whatsapp-media/{message_type}/{media_id}{file_extension}"
                    else:
                        s3_key = f"whatsapp-media/{message_type}/"

                    self._logger.debug("Uploading media to s3.")
                    # Retrieve media from WhatsApp and store in S3 using AWS End User Messaging Social
                    response = self._socialmessaging_client.get_whatsapp_message_media(
                        mediaId=media_id,
                        originationPhoneNumberId=self._settings.phone_number_id,
                        destinationS3File={
                            'bucketName': self._settings.s3_bucket_name,
                            'key': s3_key
                        }
                    )

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
                        caption = self._kms_client.encrypt_message(caption)

                    # Save the media URL in the database
                    cursor.execute(
                        "INSERT INTO messages (conversation_id, type, message, metadata, sns_message_id) VALUES (%s, %s, %s, %s, %s)",
                        (conversation_id, message_type, caption, metadata, message_id)
                    )

                    if new_convo is False:
                        cursor.execute(
                            "UPDATE conversations set `read`=0 where id = %s", (conversation_id,)
                        )

                    self._db_handler._conn.commit()
                    
            return {"statusCode": 200, "body": json.dumps({"message": "Message stored successfully"})}

        except Exception as e:
            print(traceback.format_exc())
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
