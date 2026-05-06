
from datetime import datetime
from unittest import result

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from app.services import reservation_service
from app.services.mock_llm_service import MockLLMService
from fastapi.responses import HTMLResponse
from app.schemas.chat import ChatMessage, ChatRequest
from app.services.db_service import ChatHistoryService
from app.core.config import settings
from app.services.scheduling_agent.graph import agent as agent_graph_builder
from app.services.reservation_service import ReservationService
from app.services.agent_service import SchedulingAgentService
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
    with open("app/static/index.html", "r",  encoding="utf-8") as f:
        return f.read()
    
@router.post("/test_agent")
async def test_agent(request: Request, chat_request: ChatRequest):
    scheduling_agent_service = SchedulingAgentService(request.app.mongodb)
    result = await scheduling_agent_service.invoke_agent(chat_request)
    return result

@router.post("/test_reservation_service")
async def test_reservation_service(request: Request, chat_request: ChatRequest):

    reservation_service = ReservationService(request.app.mongodb)
    await reservation_service.create_indexes()
    result = await reservation_service.create_reservation({
    "name": "Abdallah",
    "doctor": "John Doe",
    "date": "2026-05-9",
    "time": "21:30"
    })
    if result["status"] == "failed":
        start = datetime.strptime("2026-05-10 9:30", "%Y-%m-%d %H:%M")
    suggestions = await reservation_service.suggest_alternatives("John Doe", start, 30) 
    return {"result": result , "suggestions": suggestions}
    