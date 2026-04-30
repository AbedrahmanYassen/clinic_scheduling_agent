
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from app.services.mock_llm_service import MockLLMService
from app.services.ollama_services import OllamaService
from fastapi.responses import HTMLResponse
from app.schemas.chat import ChatMessage, ChatRequest
from app.services.db_service import ChatHistoryService
from app.core.config import settings
router = APIRouter()


    
@router.post("/chat")
async def chat_endpoint(request: Request, chat_request: ChatRequest):
    session_id = chat_request.session_id

    db_service = ChatHistoryService(request.app.mongodb)
    service = request.app.state.llm_service
    
    if settings.Electricity_Off:
        response = StreamingResponse(service.chat_stream(), media_type="text/event-stream")
    else:
        await db_service.summarize_and_clean(session_id)
        await db_service.save_message(session_id, chat_request.messages[-1])
        response = StreamingResponse(
            service.chat_stream(chat_request.messages, session_id=session_id, db_service=db_service),
            media_type="text/event-stream"
        )
    return response


@router.get("/", response_class=HTMLResponse)
async def get_index():
    with open("app/static/index.html", "r") as f:
        return f.read()
