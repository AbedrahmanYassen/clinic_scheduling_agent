from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.schemas.chat import AppoinementInfo

TZ = ZoneInfo(settings.TIME_ZONE)


class ConversationMemoryService:

    def __init__(self, db):

        self.collection = db["conversation_memory"]

    async def update_memory(
        self,
        session_id: str,
        entities
    ):

        update_fields = {
            "updated_at": datetime.now(TZ)
        }

        set_on_insert = {
            "created_at": datetime.now(TZ),
            "session_id": session_id
        }

        # Name
        if getattr(entities, "name", None):
            update_fields["name"] = entities.name

        # Date
        if getattr(entities, "date", None):
            update_fields["date"] = entities.date

        # Time
        if getattr(entities, "time", None):
            update_fields["time"] = entities.time

        symptoms = getattr(entities, "symptoms", None)
        print("update_fields:", update_fields)
        update_query = {
            "$set": update_fields,
            "$setOnInsert": set_on_insert
        }


        if symptoms:
            update_query["$addToSet"] = {
                "symptoms": {
                    "$each": symptoms
                }
            }

        await self.collection.update_one(
            {"session_id": session_id},
            update_query,
            upsert=True
        )

    async def get_memory(self, session_id: str):

        memory = await self.collection.find_one({
            "session_id": session_id
        })

        return memory or {}

    async def clear_memory(self, session_id: str):

        await self.collection.delete_one({
            "session_id": session_id
        })
    async def merge_entities_with_memory(
    self,
    session_id: str,
    entities : AppoinementInfo
    ):

        memory = await self.get_memory(session_id)

        return AppoinementInfo.model_validate({
            "name": entities.name or memory.get("name"),
            "date": entities.date or memory.get("date"),
            "time": entities.time or memory.get("time"),
            # "symptoms": (
            #     entities.symptoms
            #     or memory.get("symptoms", [])
            # )
    })