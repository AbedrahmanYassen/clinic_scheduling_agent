from app.services.reservation_service import ReservationService
from app.services.scheduling_agent.graph import agent as agent_graph_builder
from app.services.scheduling_agent.state import AgentState
from fastapi.encoders import jsonable_encoder
from app.services.chat_history_service import ChatHistoryService
from app.schemas.chat import ChatMessage
class SchedulingAgentService    :
    def __init__(self, db, session_id: str = None):
        self.reservation_service = ReservationService(db, session_id=session_id)
        self.db = db

    async def invoke_agent(self, chat_request):
        db_service = ChatHistoryService(self.db)
        message_object = ChatMessage(role=chat_request.messages[-1].role, content=chat_request.messages[-1].content)
        await db_service.save_message(chat_request.session_id, message_object)
        summary = await db_service.get_latest_n(chat_request.session_id, 5)
        result = await agent_graph_builder.ainvoke({"messages": chat_request.messages, "reservation": self.reservation_service, "session_id": chat_request.session_id, "summary": summary})
        png_data = agent_graph_builder.get_graph().draw_mermaid_png()


        with open("langgraph.png", "wb") as f:
            f.write(png_data)

        print("Saved!")


        return {
            "response" : result.get("response", ""),
            "entities" : jsonable_encoder(result.get("entities", {})), 
            "status" : result.get("status", "") , 
                "missing_fields": result.get("missing_fields", [])  
        }
    
    