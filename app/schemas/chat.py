from pydantic import BaseModel
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str 
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    session_id: Optional[str] = None

class AppoinementInfo(BaseModel):
    name: Optional[str] = None
    service: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None