import datetime
from app.services.calendar.client import calendar_client

class CalendarService:
    def __init__(self):
        self.client = calendar_client

    def create_event(self, summary: str, start_time: datetime.datetime, end_time: datetime.datetime, 
                     description: str = "", recurrence: list = None, reminders: dict = None):
        """Creates an event in the primary calendar."""
        service = self.client.get_service()
        
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Asia/Dushanbe',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Asia/Dushanbe',
            },
        }

        if recurrence:
            event['recurrence'] = recurrence
        
        if reminders:
            event['reminders'] = reminders

        event = service.events().insert(calendarId='primary', body=event).execute()
        return event.get('htmlLink')

    def list_events(self, max_results=10):
        """Lists upcoming events for today and tomorrow."""
        service = self.client.get_service()
        
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        
        events_result = service.events().list(
            calendarId='primary', timeMin=now,
            maxResults=max_results, singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        return events

# Singleton
calendar_service = CalendarService()
