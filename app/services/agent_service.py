from app.services.reservation_service import ReservationService
from app.services.scheduling_agent.graph import agent as agent_graph_builder
from app.services.scheduling_agent.state import AgentState
from fastapi.encoders import jsonable_encoder

class SchedulingAgentService    :
    def __init__(self, db, session_id: str = None):
        self.reservation_service = ReservationService(db, session_id=session_id)

    async def invoke_agent(self, chat_request):
        result = await agent_graph_builder.ainvoke({"messages": chat_request.messages, "reservation": self.reservation_service, "session_id": chat_request.session_id})
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
    
    