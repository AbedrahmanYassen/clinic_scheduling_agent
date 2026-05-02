from app.services.scheduling_agent.state import AgentState
from app.services.scheduling_agent.nodes import intent_node, extract_node, validate_node, availability_node, booking_node , get_user_info
from langgraph.graph import StateGraph, END

builder = StateGraph(AgentState)

builder.add_node("intent", intent_node)
builder.add_node("get_user_info", get_user_info)
builder.add_node("extract_node", extract_node)
# builder.add_node("validate", validate_node)
# builder.add_node("availability", availability_node)
# builder.add_node("book", booking_node)

builder.set_entry_point("intent")

# builder.add_conditional_edges("intent", route_intent)
builder.add_edge("intent", "get_user_info")
# builder.add_edge("validate", "availability")
# builder.add_edge("availability", "book")
# builder.add_edge("book", "respond")
builder.add_edge("get_user_info", "extract_node")
builder.add_edge("extract_node", END)

agent = builder.compile()