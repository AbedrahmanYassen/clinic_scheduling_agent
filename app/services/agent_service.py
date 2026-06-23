from app.services.reservation_service import ReservationService
from app.services.scheduling_agent.graph import agent as agent_graph_builder
from app.services.scheduling_agent.state import AgentState
from fastapi.encoders import jsonable_encoder
from app.services.chat_history_service import ChatHistoryService
from app.schemas.chat import ChatMessage
from app.services.persistent_short_memory import ConversationMemoryService
from app.services.summary_service import SummaryService


class SchedulingAgentService:
    def __init__(self, db, session_id: str = None):
        self.reservation_service = ReservationService(db, session_id=session_id)
        self.db = db

    async def invoke_agent(self, chat_request):
        db_service = ChatHistoryService(self.db)
        conversation_memory_service = ConversationMemoryService(self.db)
        message_object = ChatMessage(
            role=chat_request.messages[-1].role,
            content=chat_request.messages[-1].content,
        )
        await db_service.save_message(chat_request.session_id, message_object)
        db_history = await db_service.get_history(chat_request.session_id)

        # last_messages = db_history[-5:-1]
        
        # history_text = "\n".join(
        #     f"{msg['role']}: {msg['content']}"
        #     for msg in last_messages
        # )
        result = await agent_graph_builder.ainvoke(
            {
                "messages": chat_request.messages,
                "reservation": self.reservation_service,
                "session_id": chat_request.session_id,
                "conversation_memory": conversation_memory_service,
                # "summary": history_text
            }
        )
        # png_data = agent_graph_builder.get_graph().draw_mermaid_png()

        # with open("langgraph.png", "wb") as f:
        #     f.write(png_data)
        if result.get("send_entities"):
            return {
                "response": result.get("response", ""),
                "entities": jsonable_encoder(result.get("entities", {})),
                "status": result.get("status", ""),
                "send_entities": result.get("send_entities"),
            }
        else:
            return {
                "response": result.get("response", ""),
                "status": result.get("status", ""),
                "send_entities": result.get("send_entities"),
            }
