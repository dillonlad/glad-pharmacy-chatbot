from fastapi import APIRouter, UploadFile, File, HTTPException, status
from botocore.exceptions import ClientError
from s3_client import S3Client, S3Settings
import secrets
import string

router = APIRouter(prefix="/passport")


def _is_jpeg_bytes(data: bytes) -> bool:
    # Basic JPEG magic number check: FF D8 FF at start
    return len(data) >= 3 and data[0] == 0xFF and data[1] == 0xD8 and data[2] == 0xFF


def _random_key(length: int = 8) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@router.post("/upload", response_model=dict)
async def upload_passport_photo(uploaded_photo: UploadFile = File(...)):
    # Validate declared content type first
    if uploaded_photo.content_type not in ("image/jpeg", "image/pjpeg"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG images are accepted."
        )

    # Read the file bytes
    data = await uploaded_photo.read()

    # Validate JPEG magic bytes
    if not _is_jpeg_bytes(data):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file does not appear to be a valid JPEG."
        )

    # Prepare S3 client
    settings = S3Settings()
    settings.form_uploads_bucket = "passport-photo-codes"
    s3_client = S3Client(settings=settings)

    # Build random 8-char key and force .jpg extension
    key = f"{_random_key(8)}"

    # Upload using the helper that sets Content-Type to image/jpeg
    try:
        s3_client.upload_jpeg_from_bytes(
            key=key,
            data=data,
            public=False,
            metadata={"original_filename": uploaded_photo.filename or ""}
        )
    except ClientError:
        # Log is already handled in the client; surface a generic error to the API client
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to upload image to storage."
        )

    return {"key": f"gladp.co/{key}"}
