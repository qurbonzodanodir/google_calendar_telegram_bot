import os.path
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.core import config
from app.services.calendar import SCOPES

class TasksService:
    def __init__(self):
        self.creds = None
        self.service = None
        self.authenticate()

    def authenticate(self):
        """Authenticates using existing token.json or credentials.json.
        (Logic duplicated from CalendarService for now to keep independent)
        """
        import json
        
        creds_path = config.settings.GOOGLE_CREDENTIALS_PATH
        token_path = config.settings.GOOGLE_TOKEN_PATH
        creds_json = config.settings.GOOGLE_CREDENTIALS_JSON
        token_json = config.settings.GOOGLE_TOKEN_JSON
        
        # 1. Load Client Info
        client_config = None
        if creds_json:
            client_info = json.loads(creds_json)
            client_config = client_info.get('installed') or client_info.get('web')
        elif os.path.exists(creds_path):
             with open(creds_path, 'r') as f:
                client_info = json.load(f)
                client_config = client_info.get('installed') or client_info.get('web')
        
        # 2. Load Token Info
        token_info = None
        if token_json:
             token_info = json.loads(token_json)
        elif os.path.exists(token_path):
            with open(token_path, 'r') as f:
                token_info = json.load(f)

        if token_info:
            # Reconstruct Credentials object using helper
            try:
                self.creds = Credentials.from_authorized_user_info(token_info, SCOPES)
            except ValueError:
                self.creds = None
        
        if not self.creds or not self.creds.valid:
             # If invalid, we rely on the user having run auth_refresh.py locally
             # In Cloud, this will fail if tokens aren't updated, which is expected behavior.
             pass

        if self.creds:
            self.service = build('tasks', 'v1', credentials=self.creds)

    def get_task_lists(self):
        """Returns a list of all task lists."""
        if not self.service:
             raise Exception("Tasks Service not authenticated.")
        
        results = self.service.tasklists().list(maxResults=30).execute()
        items = results.get('items', [])
        return [{'id': item['id'], 'title': item['title']} for item in items]

    def get_tasks(self, tasklist_id: str = '@default', show_completed: bool = False):
        """Returns pending tasks from a specific list."""
        if not self.service:
             raise Exception("Tasks Service not authenticated.")
        
        results = self.service.tasks().list(
            tasklist=tasklist_id,
            maxResults=50,
            showCompleted=show_completed,
            showHidden=show_completed
        ).execute()
        
        return results.get('items', [])

    def complete_task(self, task_id: str, tasklist_id: str = '@default'):
        """Marks a task as completed."""
        if not self.service:
             raise Exception("Tasks Service not authenticated.")
        
        # To complete, we update status to 'completed'
        task = {
            'id': task_id,
            'status': 'completed'
        }
        
        self.service.tasks().update(
            tasklist=tasklist_id,
            task=task_id,
            body=task
        ).execute()

    def create_task(self, title: str, notes: str = "", due: str = None, tasklist_id: str = '@default'):
        """Creates a task in the specified list."""
        if not self.service:
             raise Exception("Tasks Service not authenticated.")

        task = {
            'title': title,
            'notes': notes
        }
        
        if due:
            # Google Tasks API requires RFC 3339 timestamp (e.g., 2023-10-01T00:00:00.000Z)
            # Ensure we have a valid datetime object and convert to UTC string + 'Z'
            try:
                if 'T' in due:
                     dt = datetime.datetime.fromisoformat(due)
                     # Convert to UTC if naive (assuming input is user's local time, but Tasks API is picky)
                     # Safest bet for API is "YYYY-MM-DDTHH:MM:SSZ"
                     task['due'] = dt.isoformat() + 'Z'
            except:
                # If parsing fails, just ignore due date to avoid crash
                pass

        result = self.service.tasks().insert(tasklist=tasklist_id, body=task).execute()
        # API response usually has 'selfLink' or 'webViewLink'. 'links' structure is rare for insert.
        return result.get('webViewLink') or result.get('selfLink') or result.get('id')

tasks_service = TasksService()
