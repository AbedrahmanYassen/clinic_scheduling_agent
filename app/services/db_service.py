from datetime import datetime
from typing import List
from app.schemas.chat import ChatMessage
from app.services.summary_service import SummaryService
from app.core.config import settings

class ChatHistoryService:
    def __init__(self, db):
        self.collection = db["chat_history"]

    async def save_message(self, session_id: str, message: ChatMessage):

        document = {
            "session_id": session_id,
            "role": message.role,
            "content": message.content,
            "timestamp": datetime.utcnow(),
        }
        await self.collection.insert_one(document)

    async def get_history(self, session_id: str) -> List[dict]:
        cursor = self.collection.find({"session_id": session_id}).sort("timestamp", 1)
        return await cursor.to_list(length=100)
    
    async def summarize_and_clean(self, session_id: str ) -> str:
        summary_service = SummaryService()
        current_history = await self.get_history(session_id)
    
        if len(current_history) <  4 or  settings.Electricity_Off:
            print("Not enough history to summarize or running in offline mode. Skipping summarization.")
            return 


        if current_history is None:
            cursor = self.collection.find({"session_id": session_id}).sort("timestamp", 1)
            history = await cursor.to_list(length=100)
        else:
            history = current_history

        formatted_text = "\n".join([f"{m['role']}: {m['content']}" for m in history])

        summary_text = await summary_service.summarize_history(formatted_text)

        await self.collection.delete_many({"session_id": session_id})

        await self.collection.insert_one({
            "session_id": session_id,
            "role": "system",
            "content": f"Summary of previous conversation: {summary_text}",
            "timestamp": datetime.utcnow(),
            "is_summary": True 
        })
        
        return summary_text
    

    
