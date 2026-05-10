from urllib import response

from app.schemas.chat import AppoinementInfo
from app.services import reservation_service
from app.services.scheduling_agent.state import AgentState
from app.services.llm_service import LLMService
from datetime import datetime
import json
llm_service = LLMService()

async def intent_node(state: AgentState):
    print("[Intent Node] State before processing:")
    print("|")
    print("|")
    last_message = state["messages"][-1].content

    intent = await llm_service.classify_intent(last_message)
    print("Classified intent:", intent)

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
    print("[Extract Node] State before processing:")
    print("|")
    print("|")
    try:
        last_message = state["messages"][-1].content

        entities_str = await llm_service.extract_entities(last_message)
        cleaned = entities_str.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()

        elif cleaned.startswith("```"):
            cleaned = cleaned.replace("```", "").strip()

        data = json.loads(cleaned)

        appointment = AppoinementInfo.model_validate(data)
        print("Validated appointment data:", appointment)

        return {"entities": appointment}    
    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)
        return {"entities": None}
    except Exception as e:
        print("Unexpected error:", e)
        return {"entities": None}                   


async def validate_node(state: AgentState):
    print("[Validate Node] State before processing:")
    print("|")
    print("|")
    missing_fields = []
    print("entities before validation:", state.get("entities", {}))
    if not state.get("entities"):
        return {
            "next_action": "missing_info",
            "response": "عذراً، لم أتمكن من استخراج المعلومات اللازمة من رسالتك. يرجى تقديم المعلومات الكاملة والصحيحة. مثال: أريد حجز موعد في 2026-05-10 الساعة 14:30. اسمي جون."
        }
    if  state["entities"].name == "null" or not state["entities"].name:
        missing_fields.append("name")

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
            "response": f"هناك بعض الحقول المفقودة أو غير الصحيحة: {', '.join(missing_fields)}. يرجى تقديم المعلومات الكاملة والصحيحة. مثال: أريد حجز موعد في 2026-05-10 الساعة 14:30. اسمي جون."
        }

    appointment_datetime = datetime.combine(
        date_obj.date(),
        time_obj.time()
    )
    print("entities after validation:", state.get("entities", {}))
  
    return {
        "next_action": "book_appointment",
        "response" : f"ممتاز! لدي جميع المعلومات اللازمة لحجز موعدك   في {date_str} الساعة {time_str}. لحظة واحدة بينما أؤكد الحجز.",
        "entities": state.get("entities"),
        }
    

def post_validation_router(state: AgentState):
    
    next_action = state.get("next_action")

    if next_action == "book_appointment":
        return "book_appointment"
    elif next_action == "missing_info":
        return "send_response"
    else:
        return "others_handler"

async def book_appointment(state: AgentState):
    print("[Book Appointment Node] State before processing:")
    print("|")
    print("|")
    print("Booking appointment with data:", state.get("entities", {}), state.get("appointment_datetime"))
    await state.get("reservation").create_indexes()
    result = await state.get("reservation").create_reservation({
    "name": state["entities"].name,
    "date": state["entities"].date,
    "time": state["entities"].time
    })

    return {
        "response": result["message"],
        "status" : result["status"]
    }

def others_handler(state: AgentState):
    print("[Others Handler] State before processing:")
    print("|")
    print("|")
    return {
        "next_action": "respond",
        "response": "عذراً، يمكنني فقط المساعدة في حجز المواعيد. لحجز موعد، يرجى تزويدي بالمعلومات التالية: الاسم، نوع الخدمة، التاريخ، والوقت.\n\nمثال: اسمي أحمد، أريد حجز موعد لفحص عام يوم 2026-05-10 الساعة 14:00."
    }

async def send_response(state: AgentState):
    print("[Send Response Node] State before processing:")
    if(state.get("status") == "success") : 
        return {
            "response": state.get("response", "عذراً، حدث خطأ ما.")
        }
    elif (state.get("status") == "failed") : 
        state.get("reservation")
        start = datetime.strptime(
        f"{state.get('entities').date} {state.get('entities').time}", "%Y-%m-%d %H:%M")
        suggestions = await state.get("reservation").suggest_alternatives( start, 30)
        return {
            "response": state.get("response", "عذراً، حدث خطأ ما.") + f" إليك بعض المواعيد البديلة المتاحة لـ : {', '.join(suggestions)}"
        }




