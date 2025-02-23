import os
import pymysql
import boto3

# Database Configuration from Environment Variables
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
SSL_ROOT = "/var/task/eu-west-2-bundle.pem"

# Fetch RDS Auth Token
def get_auth_token():
    client = boto3.client('rds', region_name="eu-west-2")
    token = client.generate_db_auth_token(
        DBHostname=DB_HOST,
        Port=3306,
        DBUsername=DB_USER,
        Region=os.getenv("AWS_REGION")
    )
    return token

def get_db_connection():
    #token = get_auth_token()
    #print(token)
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
        port=3306,
        cursorclass=pymysql.cursors.DictCursor,
        #ssl={'ca': SSL_ROOT}  # Ensure you have the CA bundle for SSL connection
    )
