from app.services.scheduling_agent.state import AgentState
from app.services.llm_service import LLMService

llm_service = LLMService()


async def intent_node(state: AgentState):
    last_message = state["messages"][-1].content

    intent = await llm_service.classify_intent(last_message)
    return {"intent": intent}
import json

async def extract_node(state: AgentState):
    last_message = state["messages"][-1].content

    extracted = await llm_service.extract_entities(last_message)
    print("Extracted entities:", extracted)
    try:
        new_entities = json.loads(extracted)
    except Exception:
        new_entities = {}

    existing_entities = state.get("entities", {})

    merged_entities = {
        **existing_entities,
        **{k: v for k, v in new_entities.items() if v}  
    }

    return {
        "entities": merged_entities
    }
async def get_user_info(state: AgentState):
    return {
        "response": "Please provide your name, date, time, doctor, and service."
    }
async def extract_node(state: AgentState):
    last_message = state["messages"][-1].content

    entities = await llm_service.extract_entities(last_message)
    return {"entities": entities}

async def validate_node(state: AgentState):
    # check missing fields
    missing = False 
    if missing:
        return {"next_action": "ask_user"}



# def validate_node(state):
#     # check missing fields
#     missing = False 
#     if missing:
#         return {"next_action": "ask_user"}
    

# def availability_node(state):
#     # query DB
#     return {"available_slots": [...]}

# def booking_node(state):
#     # write to DB
#     return {"confirmation": "..."}





