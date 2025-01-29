from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline
import boto3
import os

# Define S3 details
s3_bucket = "gladbot-model"
s3_model_folder = "v1/qa_model"
local_model_path = "./s3_chatbot_model"

# Create an S3 client
s3 = boto3.client("s3")

# Download model from S3 to local folder
if not os.path.exists(local_model_path):
    os.makedirs(local_model_path)
    for obj in s3.list_objects_v2(Bucket=s3_bucket, Prefix=s3_model_folder)["Contents"]:
        s3_key = obj["Key"]
        local_file_path = os.path.join(local_model_path, os.path.basename(s3_key))
        s3.download_file(s3_bucket, s3_key, local_file_path)

# Load the model
qa_pipeline = pipeline("question-answering", model="./s3_chatbot_model")

# Initialize FastAPI app
app = FastAPI()

# Define the request schema
class QARequest(BaseModel):
    question: str
    context: str

# Define the endpoint for question answering
@app.post("/qa")
async def get_answer(request: QARequest):
    """
    Accepts a question and context, and returns the model's answer.
    """
    try:
        result = qa_pipeline({"question": request.question, "context": request.context})
        return {
            "answer": result["answer"],
            "score": result["score"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Example root endpoint
@app.get("/")
async def root():
    return {"message": "Hugging Face Model API is running!"}
