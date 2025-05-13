from pydantic_settings import BaseSettings
from wp_db_handler import DBHandler
from s3_client import S3Client, S3Settings
from email import policy
from email.parser import BytesParser
import re
from logging import getLogger
import traceback
from datetime import datetime
from pytz import utc
from webpush_client import WebpushClient

class VoicemailSettings(BaseSettings):

    class Config:
        env_prefix = "voicemail_"
        case_sensitive = False

    sender_email: str = "voicemail@cloudtelecomservices.co.uk"
    s3_bucket: str = "glad-voicemail"
    s3_prefix: str = "unhandled"
    subject_format: str = "V-Mail from {caller_id} {phone_number} to {inbox} {extension}"
    subject_re_patterns: str = r"V-Mail from (.+?) (anonymous|[\d\s\+]+) to (.+) (\S+)$"
    silent_push: bool = False

class VoicemailManager:

    def __init__(self, db_handler):

        self._db_handler: DBHandler = db_handler
        self._settings = VoicemailSettings()
        s3_settings = S3Settings()
        s3_settings.form_uploads_bucket = "glad-voicemail"
        self._s3_client: S3Client = S3Client(settings=s3_settings)
        self._logger = getLogger("fastapi")

    def get_total_unread_voicemails(self):
        voicemails = self._db_handler.fetchone("""SELECT COUNT(id) as `count` from `voicemails` where `read`=0""")
        return voicemails["count"]
    
    def regenerate_voicemails(self):
        """
        Regenerate presigned URLs.
        """

        voicemails = self._db_handler.fetchall("""
                                SELECT sites.name as `site_name`, inboxes.name as `inbox_name`, vmails.number, vmails.filename, vmails.presigned_url, vmails.expiry, vmails.created, vmails.id as `voicemail_id`
                                FROM dashboard_sites sites
                                INNER JOIN voicemail_inboxes inboxes ON sites.id = inboxes.site_id
                                INNER JOIN voicemails vmails on inboxes.id = vmails.inbox_id
                                WHERE vmails.read = 0
                                """)
        
        unread_voicemails = {}
        current_timestamp = int(datetime.now(tz=utc).timestamp())
        for voicemail in voicemails:

            return_voicemail = voicemail.copy()
            if voicemail["inbox_name"] not in unread_voicemails:
                unread_voicemails[voicemail["inbox_name"]] = []

            presigned_url = self._s3_client.get_form_presigned_url(voicemail["filename"])
            return_voicemail["presigned_url"] = presigned_url
            url_expiry = current_timestamp + self._s3_client.presigned_url_expiry
            update_sql = "UPDATE voicemails set presigned_url='%s', expiry=%s where id=%s" % (presigned_url, url_expiry, voicemail["voicemail_id"],)
            self._db_handler.execute(update_sql, True)

            unread_voicemails[voicemail["inbox_name"]].append(return_voicemail)

        return unread_voicemails


    def get_all_unread_voicemails(self, exclude_id = None):
        """
        Get all unread voicemails.
        """

        voicemails = self._db_handler.fetchall("""
                                  SELECT sites.name as `site_name`, inboxes.name as `inbox_name`, vmails.number, vmails.filename, vmails.presigned_url, vmails.expiry, vmails.created, vmails.id as `voicemail_id`
                                  FROM dashboard_sites sites
                                  INNER JOIN voicemail_inboxes inboxes ON sites.id = inboxes.site_id
                                  INNER JOIN voicemails vmails on inboxes.id = vmails.inbox_id
                                  WHERE vmails.read = 0
                                  """)
        unread_voicemails = {}
        current_timestamp = int(datetime.now(tz=utc).timestamp())
        for voicemail in voicemails:

            return_voicemail = voicemail.copy()
            if voicemail["inbox_name"] not in unread_voicemails:
                unread_voicemails[voicemail["inbox_name"]] = []

            if voicemail["presigned_url"] is not None:
                if current_timestamp < voicemail["expiry"]:
                    return_voicemail["presigned_url"] = voicemail["presigned_url"]
                else:
                    presigned_url = self._s3_client.get_form_presigned_url(voicemail["filename"])
                    return_voicemail["presigned_url"] = presigned_url
                    update_sql = "UPDATE voicemails set presigned_url='%s' where id=%s" % (presigned_url, voicemail["voicemail_id"],)
                    self._db_handler.execute(update_sql, True)
            else:
                presigned_url = self._s3_client.get_form_presigned_url(voicemail["filename"])
                return_voicemail["presigned_url"] = presigned_url
                url_expiry = current_timestamp + self._s3_client.presigned_url_expiry
                update_sql = "UPDATE voicemails set presigned_url='%s', expiry=%s where id=%s" % (presigned_url, url_expiry, voicemail["voicemail_id"],)
                self._db_handler.execute(update_sql, True)

            if (exclude_id is not None and voicemail["voicemail_id"] != exclude_id) or exclude_id is None:
                unread_voicemails[voicemail["inbox_name"]].append(return_voicemail)

        return unread_voicemails


    def process_subject(self, subject):

        match = re.match(self._settings.subject_re_patterns, subject)
        if match:
            caller_id = match.group(1)
            phone_number = match.group(2)
            inbox = match.group(3)
            extension = match.group(4)

            return caller_id, phone_number, inbox, extension

        else:
            self._logger.debug("No match")

            return None, None, None, None

    def scan_voicemails(self):
        """
        Scan for new voicemails in unhandled folder in s3.
        """

        self._db_handler.start_session()

        voicemails = self._s3_client.list_all_objects(self._settings.s3_prefix)
        self._logger.debug(voicemails)

        webpush_client = WebpushClient(db_handler=self._db_handler)

        if len(voicemails) == 0:
            return
        
        inboxes = self._db_handler.fetchall("SELECT sites.name as `site_name`, inboxes.id, inboxes.site_id, inboxes.extension, inboxes.name, inboxes.s3_prefix from voicemail_inboxes inboxes inner join dashboard_sites sites on inboxes.site_id=sites.id")

        site_voicemails = {
            _inbox["site_name"]: 0
            for _inbox in inboxes
        }
        for voicemail_key in voicemails:

            email_obj = self._s3_client.get_object(key=voicemail_key)
            if email_obj:
                email_bytes = email_obj["Body"].read()
                # Parse the email
                msg = BytesParser(policy=policy.default).parsebytes(email_bytes)
                self._logger.debug(msg["subject"], msg["from"])
                caller_id, phone_number, inbox, extension = self.process_subject(msg["subject"])
                if caller_id is None:
                    self._logger.debug("caller id is none")
                    continue
                # Extract attachments
                for part in msg.iter_attachments():
                    filename = part.get_filename()
                    self._logger.debug("filename", filename)
                    if filename:
                        attachment_content = part.get_payload(decode=True)
                        # Save attachment to S3
                        attachment_key = f"attachments/{extension}/{filename}"
                        self._s3_client.put_object(
                            key=attachment_key,
                            content=attachment_content
                        )
                        voicemail_inbox = next((_inbox for _inbox in inboxes if int(_inbox["extension"]) == int(extension)), None)
                        if voicemail_inbox is None:
                            self._logger.debug("Couldn't find inbox")
                            continue

                        site_voicemails[voicemail_inbox["site_name"]] += 1
                        self._db_handler.execute("INSERT INTO voicemails (inbox_id, number, filename) values (%s, '%s', '%s')" % (voicemail_inbox["id"], phone_number, attachment_key))
                        self._db_handler.commit()
                        self._logger.debug(f"Saved attachment: {filename} to glad-voicemail")
            
            self._s3_client.delete_object(voicemail_key)

        if self._settings.silent_push is True:
            self._db_handler.end_session()
            return
        
        for _site in site_voicemails:
            if site_voicemails[_site] > 0:
                try:
                    webpush_client.send_push(
                        "You have new voicemails",
                        f"You have {site_voicemails[_site]} new voicemails. Please open the dashboard and check.",
                        [_site]
                    )
                except:
                    self._logger.exception(traceback.format_exc())

        self._db_handler.end_session()