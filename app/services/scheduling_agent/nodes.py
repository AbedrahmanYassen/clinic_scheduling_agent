from app.schemas.chat import AppoinementInfo
from app.services.scheduling_agent.state import AgentState
from app.services.llm_service import LLMService
from datetime import datetime
from typing import Literal
import json

llm_service = LLMService()

async def intent_node(state: AgentState):
    last_message = state["messages"][-1].content

    intent = await llm_service.classify_intent(last_message)

    return {
        "intent": intent.lower()
    }



def route_intent(state: AgentState):
    intent = state.get("intent", "")

    if "book" in intent:
        return "extract_node"
    else:
        return "others_handler"


async def extract_node(state: AgentState):
    last_message = state["messages"][-1].content

    entities = await llm_service.extract_entities(last_message)
    data = json.loads(entities)
    appointment = AppoinementInfo.model_validate(data)
    return {"entities": appointment}

VALID_DOCTORS = ["Dr. Ahmed", "Dr. Sara", "Dr. Ali"]

async def validate_node(state: AgentState):
    missing_fields = []
    print("entities before validation:", state.get("entities", {}))
    if  state["entities"].name == "null" or not state["entities"].name:
        missing_fields.append("name")

    doctor = state["entities"].doctor
    if not doctor or doctor == "null" :
        missing_fields.append("doctor")

    date_str = state["entities"].date
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    except:
        missing_fields.append("date")

    time_str = state["entities"].time
    try:
        time_obj = datetime.strptime(time_str, "%H:%M")
    except:
        missing_fields.append("time")

    if missing_fields:
        print("Missing or invalid fields:", missing_fields)
        return {
            "next_action": "missing_info",
            "response": f"There are some missing or incorrect fields: {', '.join(missing_fields)}. Please provide the whole correct information.example: I want to book an appointment with Dr. Ahmed on 2026-05-10 at 14:30. My name is John.أريد حجز موعد مع د. أحمد في 2026-05-10 الساعة 14:30. اسمي جون"
        }

    appointment_datetime = datetime.combine(
        date_obj.date(),
        time_obj.time()
    )
    print("entities after validation:", state.get("entities", {}))

    return {
        "next_action": "book_appointment",
        "response" : f"Great! I have all the information I need to book your appointment with {doctor} on {date_str} at {time_str}. Just a moment while I confirm the booking.",
        "entities": {
            "name": state.get("entities", {}).name,
            "doctor": doctor,
            "service": state.get("entities", {}).service, 
            "date": state.get("entities", {}).date, 
            "time": state.get("entities", {}).time    
        }
    }
def post_validation_router(state: AgentState):
    next_action = state.get("next_action")

    if next_action == "book_appointment":
        return "book_appointment"
    elif next_action == "missing_info":
        return "send_response"
    else:
        return "others_handler"

def book_appointment(state: AgentState):
    print("Booking appointment with data:", state.get("entities", {}), state.get("appointment_datetime"))
    return {
        "next_action": "send_response",
        "response": f"Your appointment with {state['entities']['doctor']} on {state['entities']['date']} at {state['entities']['time']} has been booked successfully."
    }

def others_handler(state: AgentState):
    return {
        "next_action": "respond",
        "response": "Sorry, I can only help with booking appointments. Please let me know if you want to book an appointment."
    }

def send_response(state: AgentState):
    return {
        "response": state.get("response", "Sorry, something went wrong.")
    }




