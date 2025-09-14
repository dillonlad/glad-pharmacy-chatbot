# lambda_function.py
import os, re, base64
import boto3
import jwt
import traceback
from jwt import InvalidTokenError

from _config import PUBLIC_PEM

S3 = boto3.client("s3")
BUCKET = os.environ["BUCKET"]
SHORT_URL_HOST = os.environ.get("SHORT_URL_HOST", "photo.co")

CODE_RE = re.compile(r"^[A-Za-z0-9_-]{4,64}$")

def _err(status, msg):
    return {"statusCode": status, "headers": {"Content-Type": "text/plain"}, "body": msg}

def _get_token_from_auth_header(h):
    if not h: return None
    parts = h.split(None, 1)  # split on first whitespace
    if len(parts) == 2 and parts[0].lower() in ("bearer", "jws", "jwt"):
        return parts[1]
    return h  # entire header is the token

def lambda_handler(event, _ctx):

    print(event)
    # 1) Extract the code from path: /{code}
    path = (event.get("requestContext", {}).get("http", {}).get("path") or "/")
    
    code = path.split("/")[-1]
    if code == "404":
        try:
            obj = S3.get_object(Bucket=BUCKET, Key=code)
            body = obj["Body"].read()
            ctype = obj.get("ContentType") or "image/jpeg"
        except S3.exceptions.NoSuchKey:
            print("no such key")
            return _err(404, "Not found")

    
        # 5) Return binary image
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": ctype,
                "Cache-Control": "public, max-age=60"
            },
            "isBase64Encoded": True,
            "body": base64.b64encode(body).decode("ascii"),
        }

    if not CODE_RE.fullmatch(code):
        print("bad photo code", code)
        return _err(400, "Bad photo code")

    # 2) Parse & verify JWS
    token = _get_token_from_auth_header((event.get("headers") or {}).get("authorization"))
    print(token)
    if not token:
        print("no token")
        return _err(401, "Missing Authorization")

    try:
        print(jwt.get_unverified_header(token))
        # HMPO’s key is RSA; algorithms likely RS256/RS512. Start with RS256.
        claims = jwt.decode(
            token,
            key=PUBLIC_PEM,
            algorithms=["RS256"],
            leeway=300,
            options={
                "require": ["sub"], 
                "verify_aud": False,    
                "verify_iat": False,
                }  # enforce sub & expiry if provided by HMPO
        )
    except InvalidTokenError:
        print("invalid token")
        print(traceback.format_exc())
        return _err(401, "Invalid token")

    # 3) Verify that `sub` is exactly the HTTPS short URL for this code
    expected_sub = f"https://{SHORT_URL_HOST}/{code}"
    if claims.get("sub") != expected_sub:
        print("subject mismatch", claims.get("sub"))
        return _err(401, "Subject mismatch")

    # (Optional) You can also enforce audience/issuer if HMPO specify them:
    # if claims.get("iss") != "expected_issuer": return _err(401, "Bad issuer")

    # 4) Fetch the image from S3
    try:
        obj = S3.get_object(Bucket=BUCKET, Key=code)
        body = obj["Body"].read()
        ctype = obj.get("ContentType") or "image/jpeg"
    except S3.exceptions.NoSuchKey:
        print("no such key")
        return _err(404, "Not found")

    
    # 5) Return binary image
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": ctype,
            "Cache-Control": "public, max-age=60"
        },
        "isBase64Encoded": True,
        "body": base64.b64encode(body).decode("ascii"),
    }
