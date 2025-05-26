from pydantic import BaseModel
from typing import List

class ChatRequest(BaseModel):
    message: str
    documentIds: List[str]

class ChatResponse(BaseModel):
    answer: str
