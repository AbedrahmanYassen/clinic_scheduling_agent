import re
from urllib import response

from pydantic import ValidationError

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
    # the next line is temporary solution to cleanup old reservations until we implement a proper background task or cron job for that
    await state.get("reservation").cleanup_old_reservations()
    last_message = state["messages"][-1].content

    intent = await llm_service.classify_intent(last_message)
    print("Classified intent:", intent)

    return {
        "intent": intent.lower()
    }



def route_intent(state: AgentState):
    intent = state.get("intent", "")

    if "book" in intent or "schedule" in intent or "reschedule" in intent or "info" in intent:
        return "extract_node"
    elif "cancel" in intent:
        return "cancel_appointment"
    else:
        return "others_handler"

async def extract_node(state: AgentState):
    print("[Extract Node] State before processing:")
    print("|")
    print("|")
    try:
        last_message = state["messages"][-1].content

        extract_object = await llm_service.extract_entities(last_message)
        
        data = extract_object["llm_response"]  # already a dict now
        print(data)

        appointment = AppoinementInfo.model_validate(data)

        await state.get("conversation_memory").update_memory(state["session_id"], appointment)
        appointment = await state.get("conversation_memory").merge_entities_with_memory(state["session_id"], appointment)
        print("Merged appointment data with memory:", appointment)
        
        return {"entities": appointment}

    except ValidationError as e:
        print("Validation error:", e)
        return {
            "entities": None,
            "send_entities": False,
            "response": "عذراً، حدث خطأ غير متوقع. يرجى المحاولة لاحقاً."
        }
    except Exception as e:
        print("Unexpected error:", e)
        return {
            "entities": None,
            "send_entities": False,
            "response": "عذراً، حدث خطأ غير متوقع. يرجى المحاولة لاحقاً."
        }
async def validate_node(state: AgentState):
    print("[Validate Node] State before processing:")
    print("|")
    print("|")
    if "info" in state.get("intent", ""):
        return {"reponse" : "شكرا لتزيدي المعلومات. هل هناك أي شيء آخر يمكنني مساعدتك به؟" , "entities": state.get("entities", {}) , "status": "success"}
    missing_fields = []
    if not state.get("entities"):
        print(state.get("entities"))
        return {
            "next_action": "missing_info",
            "response": "عذراً، لم أتمكن من استخراج المعلومات اللازمة من رسالتك. يرجى تقديم المعلومات الكاملة والصحيحة. مثال: أريد حجز موعد في 2026-05-10 الساعة 14:30. اسمي جون.",
            "send_entities" : False 
        }
    
    if  not state["intent"] == "reschedule" and (state["entities"].name == "null" or not state["entities"].name):
        missing_fields.append("name")

    print("entities after merging with memory:", state.get("entities", {}))

    if state["entities"].date in [None, "null"] :
        missing_fields.append("date")

    if state["entities"].time in [None, "null"] :
        missing_fields.append("time")

    if missing_fields  :
        print("Missing or invalid fields:", missing_fields)
        return {
            "next_action": "missing_info",
            "response": f"هناك بعض الحقول المفقودة أو غير الصحيحة: {', '.join(missing_fields)}. يرجى تقديم المعلومات الكاملة والصحيحة. مثال: أريد حجز موعد في 2026-05-10 الساعة 14:30. اسمي جون.",
            "send_entities" : False 
        }


  
    return {
        "entities": state.get("entities"),
        }
    

def post_validation_router(state: AgentState):
    
    next_action = state.get("next_action")

    if "book" in state.get("intent", "") :
        return "book_appointment"
    elif "reschedule" in state.get("intent", ""):
        return "reschedule_appointment"
    elif next_action == "missing_info":
        return "send_response"
    else:
        return "others_handler"

async def book_appointment(state: AgentState):
    print("[Book Appointment Node] State before processing:")
    print("|")
    print("|")
    print("Booking appointment with data:", state.get("entities", {}), state.get("appointment_datetime"))
    try:
        await state.get("reservation").create_indexes()
        result = await state.get("reservation").create_reservation({
        "name": state["entities"].name,
        "date": state["entities"].date,
        "time": state["entities"].time
        })
        return {
        "response": result["message"],
        "send_entities" : True , 
        "status" : result["status"]
    }
    except Exception as e:
        print("Error during booking:", e)
        return {
            "response": "عذراً، حدث خطأ أثناء محاولة حجز موعدك. يرجى المحاولة مرة أخرى لاحقاً.",
            "status": "failed", 
            "send_entities" : False 
        }
 

async def others_handler(state: AgentState):
    print("[Others Handler] State before processing:")
    print("|")
    print("|")
    try : 
        reservation = await state.get("reservation").get_reservation(session_id=state.get("session_id"))
        if reservation and "appointment_info" in state.get("intent"):
            return {
                "entities": reservation,
                "response": "إليك حجزك",
                "status" : "success",
                "send_entities" : True 
            }
        elif  "appointment_info" in state.get("intent"): 
            return {
                "entities": None,
                "response": "ليس لديك أي حجوزات"  , 
                "status" :"success", 
                "send_entities" : False 
            }
        else : 
            result = await llm_service.others_llm(state["messages"][-1].content)

    except Exception as e:
        print("Error in others_handler:", e)
        result = "عذراً، حدث خطأ أثناء معالجة طلبك. يرجى المحاولة مرة أخرى لاحقاً."
    return {
        "next_action": "respond",
        "response": result, 
        "send_entities" : False 
    }
    
async def send_response(state: AgentState):
    print("[Send Response Node] State before processing:")
    try : 
        if(state.get("status") == "success") : 
            return {
                "response": state.get("response", "عذراً، حدث خطأ ما.")
            }
        elif (state.get("status") == "failed") : 
            start = datetime.strptime(
            f"{state.get('entities').date} {state.get('entities').time}", "%Y-%m-%d %H:%M")
            suggestions = await state.get("reservation").suggest_alternatives( start, 30)
            return {
                "response": state.get("response", "عذراً، حدث خطأ ما.") + suggestions
            }
    except Exception as e:
        print("Error in send_response:", e)
        return {
            "response": state.get("response", "عذراً، حدث خطأ ما.")
        }
async def cancel_appointment(state: AgentState):
    print("[Cancel Appointment Node] State before processing:")
    print("|")
    print("|")
    try:
        result = await state.get("reservation").cancel_reservation()

        return {
        "response": result["message"],
        "status": result["status"]
        }
    except Exception as e:
        print("Error during cancellation:", e)
        return {
            "response": "عذراً، حدث خطأ أثناء محاولة إلغاء موعدك. يرجى المحاولة مرة أخرى لاحقاً.",
            "status": "failed"
        }
async def reschedule_appointment(state: AgentState):
    print("[Reschedule Appointment Node] State before processing:")
    print("|")
    print("|")
    try : 
        result = await state.get("reservation").reschedule_reservation(state.get("entities"))
   
        return {
        "response": result["message"],
        "status": result["status"]}
    
    except Exception as e:
        print("Error during rescheduling:", e)
        return {
            "response":" حاول تزويدي بالتاريخ و الوقت الذي تريد تغيير الحجز له",
            "status": "failed"
        }




