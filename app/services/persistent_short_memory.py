from datetime import datetime, date
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.schemas.chat import AppoinementInfo

TZ = ZoneInfo(settings.TIME_ZONE)


class ConversationMemoryService:

    def __init__(self, db):
        self.collection = db["conversation_memory"]

    def _is_date_stale(self, memory: dict) -> bool:
        """Return True if the memory was last updated before today."""
        created_at = memory.get("created_at")
        if not created_at:
            return False
        # Handle both aware and naive datetimes
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=TZ)
        return created_at.date() < datetime.now(TZ).date()
    async def update_intent(self, session_id: str, intent: str):
        await self.collection.update_one(
            {"session_id": session_id},
            {"$set": {"intent": intent, "updated_at": datetime.now(TZ)}},
            upsert=True
        )
    async def get_intent(self, session_id: str) -> str:
        memory = await self.collection.find_one({"session_id": session_id})
        if not memory:
            return None
        return memory.get("intent")
    async def update_memory(self, session_id: str, entities):
        update_fields = {
            "updated_at": datetime.now(TZ)
        }

        set_on_insert = {
            "created_at": datetime.now(TZ),
            "session_id": session_id
        }

        if getattr(entities, "name", None):
            update_fields["name"] = entities.name

        if getattr(entities, "date", None):
            update_fields["date"] = entities.date

        if getattr(entities, "time", None):
            update_fields["time"] = entities.time

        symptoms = getattr(entities, "symptoms", None)

        update_query = {
            "$set": update_fields,
            "$setOnInsert": set_on_insert
        }

        if symptoms:
            update_query["$addToSet"] = {
                "symptoms": {"$each": symptoms}
            }

        await self.collection.update_one(
            {"session_id": session_id},
            update_query,
            upsert=True
        )


    async def get_memory(self, session_id: str) -> dict:
        memory = await self.collection.find_one({"session_id": session_id})
        if not memory:
            return {}

        # Clear stale date from memory if it was set on a previous day
        if self._is_date_stale(memory) and "date" in memory:
            await self.collection.update_one(
                {"session_id": session_id},
                {"$unset": {"date": "", "time": ""}, "$set": {"created_at": datetime.now(TZ)}}
            )
            memory.pop("date")
            memory.pop("time")
        return memory

    async def clear_memory(self, session_id: str):
        await self.collection.delete_one({"session_id": session_id})

    async def merge_entities_with_memory(
        self,
        session_id: str,
        entities: AppoinementInfo
    ):
        memory = await self.get_memory(session_id)

        return AppoinementInfo.model_validate({
            "name": entities.name or memory.get("name"),
            "date": entities.date or memory.get("date"),
            "time": entities.time or memory.get("time"),
        })