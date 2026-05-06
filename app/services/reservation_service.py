from datetime import datetime, timedelta
from tracemalloc import start
from typing import List, Optional
from pymongo.errors import DuplicateKeyError
import pytz
from datetime import datetime, time


class ReservationService:
    def __init__(self, db):
        self.collection = db["reservations"]


    async def create_indexes(self):
        # Prevent exact duplicate start times per doctor
        await self.collection.create_index(
            [("doctor", 1), ("start_time", 1)],
            unique=True
        )
    def _build_datetime(self, date: str, time: str) -> datetime:
        return datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

    async def _has_conflict(self, doctor: str, start: datetime, end: datetime) -> bool:
        conflict = await self.collection.find_one({
            "start_time": {"$lt": end},
            "end_time": {"$gt": start}
        })
        print("Conflict check:", conflict)
        return conflict is not None
    def _is_within_working_hours(self, start: datetime, end: datetime) -> bool:

        GAZA_TZ = pytz.timezone("Asia/Gaza")

        WORK_START = time(9, 0)   
        WORK_END = time(17, 0)    
        start_local = start.astimezone(GAZA_TZ)
        end_local = end.astimezone(GAZA_TZ)

        if start_local.weekday() == 4:
            return False

        if not (WORK_START <= start_local.time() < WORK_END):
            return False

        if not (WORK_START < end_local.time() <= WORK_END):
            return False

        return True
    async def create_reservation(self, appointment_info: dict) -> dict:
        name = appointment_info.get("name")
        doctor = appointment_info.get("doctor")
        date = appointment_info.get("date")
        time = appointment_info.get("time")
        service = appointment_info.get("service")

        if not all([name, doctor, date, time]):
            return {
                "status": "failed",
                "message": "Missing required fields"
            }

        start_time = self._build_datetime(date, time)

        end_time = start_time + timedelta(minutes=30)

        if await self._has_conflict(doctor, start_time, end_time):
            return {
                "status": "failed",
                "message": "This time overlaps with another appointment"
            }
        if not self._is_within_working_hours(start_time, end_time):
            return {
                "status": "failed",
                "message": "Appointment must be within working hours (9am-5pm, Sunday-Thursday)"
            }

        document = {
            "name": name,
            "doctor": doctor,
            "start_time": start_time,
            "end_time": end_time,
            "service": service,
            "created_at": datetime.utcnow()
        }

        try:
            await self.collection.insert_one(document)
            return {
                "status": "success",
                "message": "Appointment booked successfully",
                "data": {
                    "doctor": doctor,
                    "start_time": start_time.isoformat()
                }
            }

        except DuplicateKeyError:
            return {
                "status": "failed",
                "message": "This time slot was just taken. Try another time."
            }

    async def get_reservations(self, name: str) -> List[dict]:
        cursor = self.collection.find({"name": name}).sort("start_time", 1)
        return await cursor.to_list(length=100)


    async def suggest_alternatives(
        self,
        doctor: str,
        start: datetime,
        duration_minutes: int = 30,
        attempts: int = 5
    ) -> List[str]:

        suggestions = []
        current = start

        for _ in range(attempts):
            current += timedelta(minutes=30)
            end = current + timedelta(minutes=duration_minutes)

            if not await self._has_conflict(doctor, current, end) and self._is_within_working_hours(current, end):
                suggestions.append(current.strftime("%Y-%m-%d %H:%M"))

        return suggestions