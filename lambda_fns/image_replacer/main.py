import boto3
import imagehash
from PIL import Image
import io
import os

# --- Configuration ---
BUCKET_NAME = 'your-bucket-name'
FOLDER = 'your-folder-prefix/'  # e.g. 'product-images/'
REFERENCE_IMAGE_PATH = 'bad_image.jpg'
REPLACEMENT_IMAGE_PATH = 'good_image.jpg'
SIMILARITY_THRESHOLD = 5  # Lower is stricter (0 = identical)

# --- Load Reference Image Hash ---
ref_img = Image.open(REFERENCE_IMAGE_PATH)
ref_hash = imagehash.phash(ref_img)

# --- Initialize S3 ---
s3 = boto3.client('s3')

# --- List Images in Folder ---
response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=FOLDER)
for obj in response.get('Contents', []):
    key = obj['Key']
    if not key.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        continue  # Skip non-image files

    # --- Download Image from S3 ---
    s3_obj = s3.get_object(Bucket=BUCKET_NAME, Key=key)
    image_bytes = s3_obj['Body'].read()
    try:
        img = Image.open(io.BytesIO(image_bytes))
    except:
        print(f"Skipping unreadable image: {key}")
        continue

    # --- Compare Image Hashes ---
    img_hash = imagehash.phash(img)
    if abs(img_hash - ref_hash) <= SIMILARITY_THRESHOLD:
        print(f"[MATCH] {key} will be replaced.")

        # --- Upload Replacement Image with Same Key ---
        with open(REPLACEMENT_IMAGE_PATH, 'rb') as replacement_file:
            s3.upload_fileobj(replacement_file, BUCKET_NAME, key)
    else:
        print(f"[OK] {key} is different.")
