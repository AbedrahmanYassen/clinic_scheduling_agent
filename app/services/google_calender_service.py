

class GoogleCalendarService:
    def __init__(self):
        pass

    def create_event(self, title, start_time, end_time, attendees=None):
        print(f"Creating event: {title} from {start_time} to {end_time} with attendees: {attendees}")
        return {"status": "success", "event_id": "12345"}

    def get_events(self, start_time, end_time):
        print(f"Retrieving events from {start_time} to {end_time}")
        return [{"event_id": "12345", "title": "Sample Event", "start_time": start_time, "end_time": end_time}]