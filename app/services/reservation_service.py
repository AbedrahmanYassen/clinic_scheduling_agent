from datetime import date, datetime, timedelta, timezone, timezone
from tracemalloc import start
from typing import List, Optional
from unittest import result
from zoneinfo import ZoneInfo
from pymongo.errors import DuplicateKeyError
from app.core.config import settings
from datetime import datetime, time, UTC

Time_Zone = ZoneInfo(settings.TIME_ZONE)


class ReservationService:
    def __init__(self, db, session_id: str = None):
        self.collection = db["reservations"]
        self.session_id = session_id

    async def create_indexes(self):
        await self.collection.create_index(
            [("session_id", 1), ("start_time", 1)], unique=True
        )

    def _build_datetime(self, date: str, time: str) -> datetime:
        return datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").replace(
            tzinfo=Time_Zone
        )

    async def _has_conflict(self, start: datetime, end: datetime) -> dict:
        booked_already = await self.collection.find_one(
            {
                "session_id": self.session_id,
            }
        )
        if booked_already:
            return {
                "conflict": True,
                "message": "لديك موعد محجوز بالفعل في هذا الوقت .",
                "type": "booked",
                "status": "failed",
            }
        conflict = await self.collection.find_one(
            {
                "start_time": {"$lt": end},
                "end_time": {"$gt": start},
            }
        )
        if conflict:
            return {
                "conflict": True,
                "message": "هذا الوقت متداخل مع موعد آخر.",
                "type": "conflict",
                "status": "failed",
            }
        print("Conflict check:", conflict)
        return {
            "conflict": False,
            "message": "لا يوجد تداخل في الموعد.",
            "type": "none",
            "status": "success",
        }

    def _is_within_working_hours(self, start: datetime, end: datetime) -> bool:

        WORK_START = time(9, 0)
        WORK_END = time(17, 0)
        start_local = start.astimezone(Time_Zone)
        end_local = end.astimezone(Time_Zone)

        if start_local.weekday() == 4:
            return False

        if not (WORK_START <= start_local.time() < WORK_END):
            return False

        if not (WORK_START < end_local.time() <= WORK_END):
            return False

        return True

    async def _is_past(self, start: datetime) -> bool:
        now = datetime.now(Time_Zone)
        return start < now

    async def create_reservation(self, appointment_info: dict) -> dict:
        name = appointment_info.get("name")
        date = appointment_info.get("date")
        time = appointment_info.get("time")
        service = appointment_info.get("service")

        if not all([name, date, time]):
            return {"status": "failed", "message": "هناك حقول مطلوبة مفقودة"}

        start_time = self._build_datetime(date, time)

        end_time = start_time + timedelta(minutes=30)
        if await self._is_past(start_time):
            return {"status": "failed", "message": "لا يمكنك حجز موعد في الماضي."}
        conflict_result = await self._has_conflict(start_time, end_time)
        if conflict_result["conflict"]:
            return conflict_result
        if not self._is_within_working_hours(start_time, end_time):
            return {
                "status": "failed",
                "message": "يجب أن يكون الموعد ضمن ساعات العمل (9 صباحاً - 5 مساءً، من الأحد إلى الخميس)",
            }

        document = {
            "name": name,
            "start_time": start_time,
            "end_time": end_time,
            "service": service,
            "session_id": self.session_id,
            "created_at": datetime.now(timezone.utc),
        }

        try:
            await self.collection.insert_one(document)
            return {
                "status": "success",
                "message": "تم حجز الموعد بنجاح",
                "data": {
                    "start_time": start_time.strftime(
                        "%Y-%m-%d %H:%M"
                    )  # ✅ clean format
                },
            }

        except DuplicateKeyError:
            return {
                "status": "failed",
                "message": "لقد تم أخذ هذه الفترة الزمنية للتو. حاول في وقت آخر.",
            }

    async def get_reservations(self, name: str) -> List[dict]:
        cursor = self.collection.find({"name": name}).sort("start_time", 1)
        return await cursor.to_list(length=100)

    async def suggest_alternatives(
        self,
        start: datetime,
        duration_minutes: int = 30,
        attempts: int = 5,
    ) -> str:

        suggestions = ""
        current = start

        for _ in range(attempts):
            current += timedelta(minutes=30)
            end = current + timedelta(minutes=duration_minutes)
            conflict_result = await self._has_conflict(current, end)
            if conflict_result["conflict"] and conflict_result["type"] == "conflict":
                suggestions += "إليك بعض المواعيد البديلة المتاحة لـ : "
            if (
                not conflict_result["conflict"]
                and conflict_result["type"] == "conflict"
                and self._is_within_working_hours(current, end)
            ):
                suggestions += current.strftime("%Y-%m-%d %H:%M") + ", "

        return suggestions

    async def cleanup_old_reservations(self):

        result = await self.collection.delete_many(
            {"start_time": {"$lt": datetime.now(Time_Zone)}}
        )

        print(f"Deleted {result.deleted_count} old reservations")

    async def cancel_reservation(self) -> dict:
        result = await self.collection.delete_one({"session_id": self.session_id})
        if result.deleted_count == 1:
            return {"status": "success", "message": "تم إلغاء الموعد بنجاح"}
        else:
            return {
                "status": "failed",
                "message": "لم يتم العثور على الموعد أو لا يمكنك إلغاؤه",
            }

    async def reschedule_reservation(
        self,
        new_date: str | None = None,
        new_time: str | None = None,
        duration_minutes: int = 30,
    ) -> dict:

        reservation = await self.collection.find_one({"session_id": self.session_id})

        if not reservation:
            return {"status": "failed", "message": "لا يوجد حجز لإعادة جدولته."}

        current_start = reservation["start_time"]

        date_part = new_date if new_date else current_start.strftime("%Y-%m-%d")

        time_part = new_time if new_time else current_start.strftime("%H:%M")

        new_start = datetime.strptime(
            f"{date_part} {time_part}", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=Time_Zone)

        new_end = new_start + timedelta(minutes=duration_minutes)

        conflict = await self.collection.find_one(
            {
                "_id": {"$ne": reservation["_id"]},
                "start_time": {"$lt": new_end},
                "end_time": {"$gt": new_start},
            }
        )

        if conflict:
            return {"status": "failed", "message": "الموعد الجديد غير متاح."}

        # Update reservation
        await self.collection.update_one(
            {"_id": reservation["_id"]},
            {
                "$set": {
                    "start_time": new_start,
                    "end_time": new_end,
                    "updated_at": datetime.now(Time_Zone),
                }
            },
        )

        return {
            "status": "success",
            "message": (
                f"تم إعادة جدولة الموعد إلى " f"{new_start.strftime('%Y-%m-%d %H:%M')}"
            ),
        }
