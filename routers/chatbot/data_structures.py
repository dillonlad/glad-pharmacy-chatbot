from pydantic import BaseModel

# Define the request schema
class QARequest(BaseModel):
    question: str
    context: str