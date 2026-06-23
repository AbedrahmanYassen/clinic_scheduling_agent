from urllib import response
from matplotlib import text
from pydantic import ValidationError
from app.schemas.chat import AppoinementInfo
from app.services import reservation_service
from app.services.scheduling_agent.state import AgentState
from app.services.llm_service import LLMService
from datetime import datetime

llm_service = LLMService()

async def intent_node(state: AgentState):
    print("[Intent Node] State before processing:")
    print("|")
    print("|")
    print("Classifying intent for message:", state["messages"][-1].content)
    await state.get("reservation").cleanup_old_reservations()
    last_message = state["messages"][-1].content

    intent = await llm_service.classify_intent(last_message , state.get("summary", ""))
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
        
        data = extract_object["llm_response"]  
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
    
    if  not ("reschedule" not in state["intent"] ) and (state["entities"].name == "null" or not state["entities"].name):
        missing_fields.append("name")

    print("entities after merging with memory:", state.get("entities", {}))

    if state["entities"].date in [None, "null"] :
        missing_fields.append("date")

    if state["entities"].time in [None, "null"] :
        missing_fields.append("time")
    if state["entities"].service in [None, "null"] :
        state["entities"].service = "عام"
    if missing_fields  :
        print("Missing or invalid fields:", missing_fields)
        return {
            "next_action": "missing_info",
            "send_entities" : False , 
            "status" : "failed"
        }


  
    return {
        "entities": state.get("entities"),
        }
    

def post_validation_router(state: AgentState):
    
    next_action = state.get("next_action")
    if next_action == "missing_info" and "reschedule" not in state.get("intent", ""):
        print("Routing to send_response due to missing info")
        return "send_response"
    elif "book" in state.get("intent", "") :
        return "book_appointment"
    elif "reschedule" in state.get("intent", ""):
        return "reschedule_appointment"
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
        "time": state["entities"].time, 
        "service": state["entities"].service
        })
        return {
        "send_entities" : True , 
        "status" : result["status"], 
        "response": result["message"],
        "next_action" : result.get("type", None) 
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
    try:
        reservation = await state.get("reservation").get_reservation(session_id=state.get("session_id"))
        print("Reservation" , reservation)
        
        if reservation and "appointment_info" in state.get("intent"):
            return {
                "entities": reservation,
                "response": "إليك حجزك",
                "status": "success",
                "send_entities": True
            }
        elif "appointment_info" in state.get("intent"):
            return {
                "entities": None,
                "response": "ليس لديك أي حجوزات",
                "status": "success",
                "send_entities": False
            }
        else:
            result = await llm_service.others_llm(state["messages"][-1].content)
            return {
                "next_action": "respond",
                "response": result,
                "send_entities": False
            }

    except Exception as e:
        print("Error in others_handler:", e)
        return {
            "next_action": "respond",
            "response": "عذراً، حدث خطأ أثناء معالجة طلبك. يرجى المحاولة مرة أخرى لاحقاً.",
            "send_entities": False
        }
async def send_response(state: AgentState):
    print("[Send Response Node] State before processing:")
    print("current state:", state)
    try : 
        if(state.get("status") == "success") : 
            return {
                "response": state.get("response", "عذراً، حدث خطأ ما.")
            }
        elif(state.get("next_action") == "missing_info") : 
            print("INside the generate missing response ")
            if state.get("entities") :
                response = llm_service.generate_missing_info_response(state.get("entities"))
                return {
                    "response":  response ,  
                }
            else :
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
    # try:
    result = await state.get("reservation").reschedule_reservation(state.get("entities"))

    if result.get("status") == "failed" and result.get("type") == "no_reservation":
        return {
            "next_action": "book_appointment",
            "response": "لم يتم العثور على حجز لإعادة جدولته. هل تود حجز موعد جديد؟",
            "send_entities": False
        }

    return {
        "response": result["message"],
        "status": result["status"]
    }

    # except Exception as e:
        # return {
        #     "response": " حاول تزويدي بالتاريخ و الوقت الذي تريد تغيير الحجز له",
        #     "status": "failed"
        # }



def post_rescheduling_router(state: AgentState):
    
    next_action = state.get("next_action")
    if next_action == "book_appointment":
        return "book_appointment"
    else:
        return "END"

