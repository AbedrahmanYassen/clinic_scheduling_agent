from app.services.scheduling_agent.state import AgentState
from app.services.scheduling_agent.nodes import *
from langgraph.graph import StateGraph, END

builder = StateGraph(AgentState)

builder.add_node("intent_node", intent_node)
builder.add_node("extract_node", extract_node)
builder.add_node("validate_node", validate_node)
builder.add_node("others_handler", others_handler)
builder.add_node("book_appointment", book_appointment)
builder.add_node("send_response", send_response)
builder.add_node("cancel_appointment", cancel_appointment)
builder.add_node("reschedule_appointment", reschedule_appointment)
builder.set_entry_point("intent_node")
builder.add_conditional_edges(
    "intent_node",
    route_intent,
    {
        "extract_node": "extract_node",
        "cancel_appointment": "cancel_appointment",
        "reschedule_appointment": "reschedule_appointment",
        "others_handler": "others_handler",
    }
)
builder.add_conditional_edges(
    "validate_node",
    post_validation_router,
    {
        "book_appointment": "book_appointment",
        "send_response": "send_response",
        "others_handler": "others_handler",
    }
)

builder.add_edge("book_appointment", "send_response")
builder.add_edge("send_response", END)
builder.add_edge("extract_node", "validate_node")
builder.add_edge("cancel_appointment", END)
builder.add_edge("reschedule_appointment", END)
agent = builder.compile()