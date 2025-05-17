import pymysql
import boto3

# -------- CONFIGURATION -------- #
# MySQL configuration
MYSQL_HOST = ''
MYSQL_PORT = 3306
MYSQL_USER = ''
MYSQL_PASSWORD = ''
MYSQL_DATABASE = ''

# AWS S3 configuration
S3_BUCKET_NAME = 'glad-voicemail'
AWS_REGION = 'eu-west-2'
# -------------------------------- #

def fetch_filenames():
    """Fetch filenames from voicemails table where read = 1"""
    connection = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT filename 
                FROM voicemails 
                WHERE `read` = 1 AND created < NOW() - INTERVAL 7 DAY""")
            results = cursor.fetchall()
            return [row[0] for row in results]
    finally:
        connection.close()

def delete_s3_objects(filenames):
    """Delete objects from S3 using the list of filenames"""
    s3 = boto3.client(
        's3',
        region_name=AWS_REGION,
    )

    objects_to_delete = [{'Key': key} for key in filenames]
    if not objects_to_delete:
        print("No files to delete.")
        return

    response = s3.delete_objects(
        Bucket=S3_BUCKET_NAME,
        Delete={'Objects': objects_to_delete}
    )
    print("Deleted objects:", response.get('Deleted', []))
    if 'Errors' in response:
        print("Errors:", response['Errors'])

def main():
    filenames = fetch_filenames()
    print(f"Found {len(filenames)} files to delete.")
    delete_s3_objects(filenames)

if __name__ == '__main__':
    main()
