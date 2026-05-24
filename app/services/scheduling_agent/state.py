from typing import TypedDict
from app.schemas.chat import AppoinementInfo
from app.services.reservation_service import ReservationService
from app.services.persistent_short_memory import ConversationMemoryService
class AgentState(TypedDict):
    session_id: str | None
    messages: list
    intent: str | None
    entities: AppoinementInfo | None
    next_action: str | None
    response: str | None
    reservation : ReservationService | None
    conversation_memory : ConversationMemoryService | None
    status : str | None
    summary : str | None
    send_entities: bool | None 


