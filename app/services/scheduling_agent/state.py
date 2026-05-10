from typing import TypedDict
from app.schemas.chat import AppoinementInfo
from app.services.reservation_service import ReservationService
class AgentState(TypedDict):
    session_id: str | None
    messages: list
    intent: str | None
    entities: AppoinementInfo | None
    next_action: str | None
    response: str | None
    reservation : ReservationService | None
    status : str | None


