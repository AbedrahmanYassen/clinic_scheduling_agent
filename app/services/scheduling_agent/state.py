from typing import TypedDict
from app.schemas.chat import AppoinementInfo
class AgentState(TypedDict):
    messages: list
    intent: str | None
    entities: AppoinementInfo | None
    next_action: str | None
    response: str | None


