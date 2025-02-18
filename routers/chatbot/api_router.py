from fastapi import APIRouter, Depends, HTTPException
import json
import boto3
from routers.chatbot.data_structures import QARequest


router = APIRouter(prefix="/chatbot")

# Define the endpoint for question answering
@router.post("/qa")
async def get_answer(qa_request: QARequest):
    """
    Accepts a question and context, and returns the model's answer.
    """

    client = boto3.client("sagemaker-runtime", region_name="eu-west-2")
    try:
        result = client.invoke_endpoint(
                    EndpointName="gladbot-distilbert",
                    ContentType="application/json",
                    Body=json.dumps({"inputs": qa_request.model_dump()}),
                )
        response = json.loads(result["Body"].read().decode("utf-8"))
        return {
            "answer": response["answer"],
            "score": response["score"]
        } 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))