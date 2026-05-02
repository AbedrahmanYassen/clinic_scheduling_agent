from typing import TypedDict

class AgentState(TypedDict):
    messages: list
    intent: str | None
    entities: dict
    appointment_data: dict
    next_action: str | None
    response: str | None