import pandas as pd
import boto3
from botocore.exceptions import ClientError

# Replace with your Cognito User Pool ID
USER_POOL_ID = 'eu-west-2_kvNlJXgmz'

# Read the Excel file
df = pd.read_excel("C:\\Users\\Dillon\\OneDrive\\Desktop\\Staff - Dillon.xlsx", header=None)  # Replace with your file path

# Initialize Cognito client
client = boto3.client('cognito-idp')


def format_name(name):
    return name.lower().title()

def update_user_attribute():
    try:
        # # Check if user exists
        # client.admin_get_user(
        #     UserPoolId=USER_POOL_ID,
        #     Username=username
        # )

        client.add_custom_attributes(
        UserPoolId=USER_POOL_ID,
        CustomAttributes=[
            {
                'Name': 'al_entitlement',
                'AttributeDataType': 'Number',  # Use 'String' if needed
                'Mutable': True,
                'Required': False,
                'NumberAttributeConstraints': {
                    'MinValue': '0',
                    'MaxValue': '100'
                }
            }
        ]
    )

    except ClientError as e:
        print(e)

# # Iterate through the rows
# for index, row in df.iterrows():
#     username = str(row[7]).strip()  # Column H
#     raw_name = str(row[2]).strip()  # Column C

#     if username and raw_name and username != 'nan':
#         formatted_name = format_name(raw_name)
update_user_attribute()