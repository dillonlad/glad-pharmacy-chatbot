from pydantic_settings import BaseSettings
import boto3
import json
from whatsapp_client import WhatsAppClient
from logging import getLogger
import traceback


class SQSSettings(BaseSettings):

    class Config:
        env_prefix = "sqs_"
        case_sensitive = False

    url: str


class SQSClient:

    def __init__(self, whatsapp_client: WhatsAppClient):
        
        self._settings = SQSSettings()
        self._sqs_client = boto3.client('sqs')
        self._whatsapp_client = whatsapp_client
        self._logger = getLogger("fastapi")

    def process_queue(self):
        """
        Process and ingest SQS queue. Messages stored in queue will all be WhatsApp related.
        """

        while True:
            try:

                response = self._sqs_client.receive_message(
                    QueueUrl=self._settings.url,
                    MaxNumberOfMessages=10,  # Process messages in batches
                    WaitTimeSeconds=5
                )

                if "Messages" in response:
                    for message in response["Messages"]:
                        try:
                            message_body = json.loads(message["Body"])
                            message_id = message_body["MessageId"]

                            try:
                                _message = json.loads(message_body["Message"])
                                webhook_entry = json.loads(_message["whatsAppWebhookEntry"])
                                self._whatsapp_client.process_incoming_message(webhook_entry, message_id)

                                # Delete processed message from SQS
                                self._sqs_client.delete_message(
                                    QueueUrl=self._settings.url,
                                    ReceiptHandle=message["ReceiptHandle"]
                                )
                            except:
                                self._logger.exception(f"Error whilst processing SQS message with id: {message_id}")
                        except:
                            self._logger.exception("Error whilst processing message from SQS")

                else:
                    break  # No messages left in queue

            except Exception as e:
                self._logger.error(traceback.format_exc())
                self._logger.error(f"Error fetching messages from SQS: {str(e)}")
                break

        self._whatsapp_client._db_handler.end_session()