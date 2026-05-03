from app.services.scheduling_agent.state import AgentState
from app.services.scheduling_agent.nodes import intent_node, extract_node  , validate_node , others_handler , route_intent , post_validation_router , book_appointment , send_response
from langgraph.graph import StateGraph, END

builder = StateGraph(AgentState)

builder.add_node("intent_node", intent_node)
builder.add_node("extract_node", extract_node)
builder.add_node("validate_node", validate_node)
builder.add_node("others_handler", others_handler)
builder.add_node("book_appointment", book_appointment)
builder.add_node("send_response", send_response)
builder.set_entry_point("intent_node")
builder.add_conditional_edges(
    "intent_node",
    route_intent,
    {
        "extract_node": "extract_node",
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
builder.add_edge("extract_node", "validate_node")
builder.add_edge("validate_node", END)

agent = builder.compile()