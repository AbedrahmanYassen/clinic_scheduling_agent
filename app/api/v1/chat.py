
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
from app.services.chat_history_service import ChatHistoryService
from app.core.config import settings
from app.services.scheduling_agent.graph import agent as agent_graph_builder
from app.services.reservation_service import ReservationService
from app.services.agent_service import SchedulingAgentService
router = APIRouter()


    
@router.post("/test_chat")
async def chat_endpoint(request: Request, chat_request: ChatRequest):
    session_id = chat_request.session_id

    scheduling_agent_service = SchedulingAgentService(db=request.app.mongodb, session_id=session_id)

    
    if settings.Electricity_Off:
        response = "⚡ النظام حالياً غير متصل بالإنترنت. يرجى المحاولة مرة أخرى لاحقاً."
    else:
        result = await scheduling_agent_service.invoke_agent(chat_request)
        response = {
            "response" : result.get("response", ""),
            "entities" : result.get("entities", {}), 
            "status" : result.get("status", "") , 
            "missing_fields": result.get("missing_fields", [])  
        }

    return response


@router.get("/", response_class=HTMLResponse)
async def get_index():
    with open("app/static/index.html", "r",  encoding="utf-8") as f:
        return f.read()
    
@router.post("/chat")
async def test_agent(request: Request, chat_request: ChatRequest):
    scheduling_agent_service = SchedulingAgentService(request.app.mongodb, session_id=chat_request.session_id)
    result = await scheduling_agent_service.invoke_agent(chat_request)
    return result

@router.post("/test_reservation_service")
async def test_reservation_service(request: Request, chat_request: ChatRequest):

    reservation_service = ReservationService(request.app.mongodb, session_id=chat_request.session_id)
    await reservation_service.create_indexes()
    result = await reservation_service.create_reservation({
    "name": "Abdallah",
    "date": "2026-05-9",
    "time": "21:30"
    })
    if result["status"] == "failed":
        start = datetime.strptime("2026-05-10 9:30", "%Y-%m-%d %H:%M")
    suggestions = await reservation_service.suggest_alternatives(start, 30) 
    formatted_suggestions = "\n".join(
        f"- {slot}" for slot in suggestions
    )

    result["message"] += f"\n\nAvailable alternatives:\n{formatted_suggestions}"
    return {"result": result}
    