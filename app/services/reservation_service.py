from datetime import date, datetime, timedelta, timezone, timezone
from tracemalloc import start
from typing import List, Optional
from unittest import result
from zoneinfo import ZoneInfo
from pymongo.errors import DuplicateKeyError
from app.core.config import settings
from datetime import datetime, time, UTC
from app.schemas.chat import AppoinementInfo
from bson import ObjectId
from datetime import datetime

Time_Zone = ZoneInfo(settings.TIME_ZONE)


class ReservationService:
    def __init__(self, db, session_id: str = None):
        self.collection = db["reservations"]
        self.session_id = session_id

    async def create_indexes(self):
        await self.collection.create_index([("start_time", 1)], unique=True)

    def _build_datetime(self, date, time):
        if hasattr(date, "strftime"):
            date = date.strftime("%Y-%m-%d")

        if hasattr(time, "strftime"):
            time = time.strftime("%H:%M")

        time = str(time)

        if len(time.split(":")) == 3:
            time = ":".join(time.split(":")[:2])

        return datetime.strptime(
            f"{date} {time}",
            "%Y-%m-%d %H:%M"
        ).replace(tzinfo=Time_Zone)

    async def _has_conflict(self, start: datetime, end: datetime) -> dict:
        booked_already = await self.collection.find_one(
            {
                "session_id": self.session_id,
            }
        )
        if booked_already:
            return {
                "conflict": True,
                "message": "لديك موعد محجوز ",
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
            return {
                "status": "failed",
                "message": "هناك حقول مطلوبة مفقودة",
                "type": "missing_info",
            }

        start_time = self._build_datetime(date, time)

        end_time = start_time + timedelta(minutes=30)
        if await self._is_past(start_time):
            return {
                "status": "failed",
                "message": "لا يمكنك حجز موعد في الماضي.",
                "type": "past_date",
            }
        conflict_result = await self._has_conflict(start_time, end_time)
        if conflict_result["conflict"]:
            return conflict_result
        if not self._is_within_working_hours(start_time, end_time):
            return {
                "status": "failed",
                "message": "يجب أن يكون الموعد ضمن ساعات العمل (9 صباحاً - 5 مساءً، من الأحد إلى الخميس)",
                "type": "working_hours",
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
                    ),  # ✅ clean format
                    type: "success",
                },
            }

        except DuplicateKeyError:
            return {
                "status": "failed",
                "message": "لقد تم أخذ هذه الفترة الزمنية للتو. حاول في وقت آخر.",
                "type": "exception",
            }

    async def get_reservation(self, session_id: str) -> AppoinementInfo | None:
        doc = await self.collection.find_one({"session_id": session_id})
        if doc is None:
            return None

        start_time: datetime = doc.get("start_time")
        if start_time:
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=ZoneInfo("UTC")).astimezone(
                    Time_Zone
                )
            else:
                start_time = start_time.astimezone(Time_Zone)

        return AppoinementInfo(
            name=doc.get("name"),
            service=doc.get("service"),
            date=start_time.strftime("%Y-%m-%d") if start_time else None,
            time=start_time.strftime("%I:%M %p") if start_time else None,
        )

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
    appointment_info: AppoinementInfo
) -> dict:

        date = appointment_info.date
        time = appointment_info.time
        name = appointment_info.name
        service = appointment_info.service

        reservation = await self.collection.find_one(
            {"session_id": self.session_id}
        )

        if not reservation:
            return {
                "status": "failed",
                "message": "لا يوجد حجز لإعادة جدولته.",
                "type": "no_reservation"
            }

        update_fields = {}
        message_parts = []

        # -------------------------
        # Existing reservation datetime
        # -------------------------
        old_start = reservation["start_time"]

        new_date = date if date else old_start.date()
        new_time = time if time else old_start.time()
        print("New date:", new_date)
        print("New time:", new_time)
        datetime_changed = bool(date or time)

        # -------------------------
        # Handle date/time updates
        # -------------------------
        if datetime_changed:

            start_time = self._build_datetime(new_date, new_time)
            end_time = start_time + timedelta(minutes=30)
            
            if await self._is_past(start_time):
                return {
                    "status": "failed",
                    "message": "لا يمكنك حجز موعد في الماضي."
                }

            if not self._is_within_working_hours(start_time, end_time):
                return {
                    "status": "failed",
                    "message": "يجب أن يكون الموعد ضمن ساعات العمل (9 صباحاً - 5 مساءً، من الأحد إلى الخميس)",
                    "type": "outside_working_hours"
                }

            conflict = await self.collection.find_one(
                {
                    "_id": {"$ne": reservation["_id"]},
                    "start_time": {"$lt": end_time},
                    "end_time": {"$gt": start_time},
                }
            )

            if conflict:
                return {
                    "status": "failed",
                    "message": "الموعد الجديد غير متاح.",
                    "type": "conflict"
                }

            update_fields["start_time"] = start_time
            update_fields["end_time"] = end_time

            message_parts.append(
                f"تم تحديث الموعد إلى {start_time.strftime('%Y-%m-%d %H:%M')}"
            )

        # -------------------------
        # Name update
        # -------------------------
        if name and name != reservation.get("name"):
            update_fields["name"] = name
            message_parts.append(f"تم تحديث الاسم إلى {name}")

        # -------------------------
        # Service update
        # -------------------------
        if service and service != reservation.get("service"):
            update_fields["service"] = service
            message_parts.append(f"تم تحديث الخدمة إلى {service}")

        # -------------------------
        # Nothing changed
        # -------------------------
        if not update_fields:
            return {
                "status": "failed",
                "message": "لا توجد بيانات جديدة للتحديث.",
                "type": "no_changes"
            }

        update_fields["updated_at"] = datetime.now(Time_Zone)

        await self.collection.update_one(
            {"_id": reservation["_id"]},
            {"$set": update_fields},
        )

        return {
            "status": "success",
            "message": "، ".join(message_parts) + ".",
            "type": "success"
        }