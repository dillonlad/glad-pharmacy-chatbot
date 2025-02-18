import boto3
import json

client = boto3.client("sagemaker-runtime", region_name="eu-west-2")

response = client.invoke_endpoint(
    EndpointName="gladbot-distilbert",
    ContentType="application/json",
    Body=json.dumps({"inputs": {"question": "What are the weekday opening hours for the Calverton branch?", "context": "Our branch in Calverton is open 9am to 6pm on weekdays. The Calverton branch is open 9am to 5pm on Saturdays. The Calverton branch is closed on Sundays."}}),
)

print(json.loads(response["Body"].read().decode()))
