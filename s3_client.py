from pydantic_settings import BaseSettings
import boto3
from botocore.exceptions import ClientError
from logging import getLogger


class S3Settings(BaseSettings):

    class Config:
        env_prefix = "s3_"
        case_sensitive = False

    form_uploads_bucket: str = "gladpharmacy-form-uploads"
    form_expiration: int = 10800


class S3Client:
    """
    Handles the retrieval of S3 objects or their presigned URLs
    """

    def __init__(self, settings: S3Settings = S3Settings()):
        
        self._settings = settings
        self._s3_client = boto3.client("s3")
        self._logger = getLogger("fastapi")

    @property
    def presigned_url_expiry(self):
        return self._settings.form_expiration

    def generate_presigned_url(self, client_method, method_parameters, expires_in):
        """
        Generate a presigned Amazon S3 URL that can be used to perform an action.

        :param client_method: The name of the client method that the URL performs.
        :param method_parameters: The parameters of the specified client method.
        :param expires_in: The number of seconds the presigned URL is valid for.
        :return: The presigned URL.
        """
        try:
            url = self._s3_client.generate_presigned_url(
                ClientMethod=client_method, Params=method_parameters, ExpiresIn=expires_in
            )
            self._logger.info("Got presigned URL: %s", url)
        except ClientError:
            self._logger.exception(
                "Couldn't get a presigned URL for client method '%s'.", client_method
            )
            raise
        return url
    
    def get_form_presigned_url(self, form_s3_key: str):
        try:
            return self.generate_presigned_url(
                client_method="get_object", 
                method_parameters={
                    "Bucket": self._settings.form_uploads_bucket, 
                    "Key": form_s3_key
                    }, 
                expires_in=self._settings.form_expiration,
                )
        except:
            return ""
        
    def list_all_objects(self, folder_name):

        response = self._s3_client.list_objects_v2(
            Bucket=self._settings.form_uploads_bucket, 
            Prefix=folder_name,
            )
        
        objects = []
        if 'Contents' in response:
            for obj in response['Contents']:
                objects.append(obj['Key'])  # Full object key (path)

        return objects
    
    def get_object(self, key):

        return self._s3_client.get_object(
            Bucket=self._settings.form_uploads_bucket, 
            Key=key,
        )
    
    def put_object(self, key, content):

        return self._s3_client.put_object(
            Bucket=self._settings.form_uploads_bucket, 
            Key=key,
            Body=content,
        )
        
    def delete_object(self, key):
        return self._s3_client.delete_object(
            Bucket=self._settings.form_uploads_bucket, 
            Key=key,
        )

    # --- NEW METHOD ---
    def upload_jpeg_from_bytes(self, key: str, data: bytes, public: bool = False, metadata: dict | None = None):
        """
        Upload an image (JPEG) to S3 from raw bytes with the correct Content-Type.

        :param key: Destination key in the bucket (e.g. 'images/photo.jpg').
        :param data: Raw JPEG bytes.
        :param public: If True, sets ACL to 'public-read'.
        :param metadata: Optional user-defined metadata dict.
        :return: The boto3 put_object response.
        :raises: botocore.exceptions.ClientError on failure.
        """
        bucket = self._settings.form_uploads_bucket

        # Light sanity check for JPEG magic bytes; log-only, do not block upload.
        if not (len(data) >= 3 and data[0] == 0xFF and data[1] == 0xD8 and data[2] == 0xFF):
            self._logger.warning("upload_jpeg_from_bytes: data does not appear to start with JPEG magic bytes.")

        params = {
            "Bucket": bucket,
            "Key": key,
            "Body": data,
            "ContentType": "image/jpeg",
        }
        if metadata:
            params["Metadata"] = metadata
        if public:
            params["ACL"] = "public-read"

        try:
            resp = self._s3_client.put_object(**params)
            self._logger.info("Uploaded JPEG to s3://%s/%s", bucket, key)
            return resp
        except ClientError:
            self._logger.exception("Failed to upload JPEG to s3://%s/%s", bucket, key)
            raise
