from pydantic_settings import BaseSettings
import boto3

from kms_client import KMSClient
from wp_db_handler import DBHandler


class WhatsAppSettings(BaseSettings):

    class Config:
        env_prefix = "whatsapp_"
        case_sensitive = False

    phone_number_id: str


class WhatsAppClient:

    def __init__(self, db_handler: DBHandler):
        
        self._kms_client = KMSClient()
        self._db_handler = db_handler
        self._socialmessaging_client = boto3.client('socialmessaging')

    def send_message(self):
        pass

    def get_channels(self):
        
        sql = """
                select conversations.id, conversations.profile_name as `title`, conversations.read as `date`, case when top_message.message is not null then top_message.message when top_message.metadata is not null then 'Multimedia' else 'No Messages' end as `subtitle`
                from conversations
                left outer join (
                    SELECT conversation_id, message, metadata 
                    FROM messages 
                    group by conversation_id
                    order by created desc
                ) top_message on conversations.id=top_message.conversation_id
                order by conversations.read desc
              """

        return self._db_handler.fetchall(sql)

    def get_conversation(self):
        pass
