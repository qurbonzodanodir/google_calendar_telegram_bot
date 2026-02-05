
import os.path
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from app.core import config

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

class CalendarService:
    def __init__(self):
        self.creds = None
        self.service = None
        self.authenticate()

    def authenticate(self):
        """Authenticates using existing token.json or credentials.json."""
        import json
        
        creds_path = config.settings.GOOGLE_CREDENTIALS_PATH
        token_path = config.settings.GOOGLE_TOKEN_PATH
        
        # Load Client Info
        if not os.path.exists(creds_path):
             raise Exception(f"Credentials file not found at {creds_path}")
             
        with open(creds_path, 'r') as f:
            client_info = json.load(f)
            # Handle both 'installed' and 'web' formats
            client_config = client_info.get('installed') or client_info.get('web')
            if not client_config:
                raise Exception("Invalid credentials.json format")
                
        # Load Token Info
        if os.path.exists(token_path):
            with open(token_path, 'r') as f:
                token_info = json.load(f)
            
            # Reconstruct Credentials object
            self.creds = Credentials(
                token=token_info.get('access_token'),
                refresh_token=token_info.get('refresh_token'),
                token_uri=client_config.get('token_uri') or "https://oauth2.googleapis.com/token",
                client_id=client_config.get('client_id'),
                client_secret=client_config.get('client_secret'),
                scopes=SCOPES
            )
        
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                 raise Exception("Token invalid or missing. Please re-authenticate via CLI first.")
            
            # Save the credentials for the next run (optional, preserving structure)
            # data_to_save = json.loads(self.creds.to_json())
            # with open(token_path, 'w') as token:
            #     token.write(json.dumps(data_to_save))

        self.service = build('calendar', 'v3', credentials=self.creds)


    def create_event(self, summary: str, start_time: datetime.datetime, end_time: datetime.datetime, 
                     description: str = "", recurrence: list = None, reminders: dict = None):
        """Creates an event in the primary calendar."""
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

        event = self.service.events().insert(calendarId='primary', body=event).execute()
        return event.get('htmlLink')

calendar_service = CalendarService()
