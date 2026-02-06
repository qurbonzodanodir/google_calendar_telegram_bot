import os.path
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from app.core import config
import logging

logger = logging.getLogger(__name__)

SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/tasks'
]

class GoogleCalendarClient:
    def __init__(self):
        self.creds = None
        self.service = None
        self.authenticate()

    def authenticate(self):
        """Authenticates using existing token.json or credentials.json."""
        creds_path = config.settings.GOOGLE_CREDENTIALS_PATH
        token_path = config.settings.GOOGLE_TOKEN_PATH
        creds_json = config.settings.GOOGLE_CREDENTIALS_JSON
        token_json = config.settings.GOOGLE_TOKEN_JSON
        
        # 1. Load Client Info (Env Var OR File)
        client_config = None
        if creds_json:
            try:
                client_info = json.loads(creds_json)
                client_config = client_info.get('installed') or client_info.get('web')
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GOOGLE_CREDENTIALS_JSON: {e}")
        elif os.path.exists(creds_path):
             with open(creds_path, 'r') as f:
                client_info = json.load(f)
                client_config = client_info.get('installed') or client_info.get('web')
        
        if not client_config:
            # We log but don't raise immediately to allow graceful failure if not needed right away
            logger.warning("Credentials missing! Set GOOGLE_CREDENTIALS_JSON env var or mapped volume.")

        # 2. Load Token Info (Env Var OR File)
        token_info = None
        if token_json:
             try:
                token_info = json.loads(token_json)
             except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GOOGLE_TOKEN_JSON: {e}")
        elif os.path.exists(token_path):
            with open(token_path, 'r') as f:
                token_info = json.load(f)

        if token_info:
            # Reconstruct Credentials object
            try:
                self.creds = Credentials.from_authorized_user_info(token_info, SCOPES)
            except ValueError:
                self.creds = None
        
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Failed to refresh token: {e}")
                    self.creds = None
            else:
                 # In Cloud Env, we cannot launch browser. Fail explicitly.
                 if creds_json:
                     logger.error("Token invalid/expired in Cloud Env. Please refresh locally and update GOOGLE_TOKEN_JSON.")
                 else:
                     logger.debug(f"creds_path={creds_path}, exists={os.path.exists(creds_path)}")
                     logger.debug(f"token_path={token_path}, exists={os.path.exists(token_path)}")
                     # raise Exception("Token invalid or missing.") # Don't crash app on start, fail on use

        if self.creds and self.creds.valid:
            self.service = build('calendar', 'v3', credentials=self.creds)
            logger.info("✅ Google Calendar Service initialized.")
        else:
            logger.warning("❌ Google Calendar Service failed to initialize.")

    def get_service(self):
        if not self.service:
            # Try to auth again if called and failed before
            self.authenticate()
            if not self.service:
                 raise Exception("Google Calendar Service is not authenticated.")
        return self.service

# Singleton
calendar_client = GoogleCalendarClient()
