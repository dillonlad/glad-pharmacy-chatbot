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