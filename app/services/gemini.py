
import json
import datetime
from google import genai
from google.genai import types
from app.core import config
import logging

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        if config.settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=config.settings.GEMINI_API_KEY)
            self.model_name = "gemini-flash-latest"
        else:
            self.client = None
            logger.warning("Gemini API Key missing!")

    async def parse_event(self, text: str, user_timezone: str = "Asia/Dushanbe"):
        """Parses natural language text into a structured JSON event."""
        if not self.client:
            raise Exception("Gemini API Key is missing in .env")

        current_time = datetime.datetime.now().isoformat()
        
        prompt = f"""
        You are a smart calendar assistant. 
        Current time: {current_time}
        User Timezone: {user_timezone}

        Extract the event details from the user's text: "{text}"

        Return a VALID JSON object with:
        - summary: Short title of the event
        - start: Start time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS) in the user's timezone.
        - end: End time in ISO 8601 format. If duration is not specified, assume 1 hour.
        - description: Any extra details.
        - recurrence: LIST of RRULE strings (RFC 5545) if the event repeats. Example: ["RRULE:FREQ=WEEKLY;BYDAY=MO"] for "Every Monday". Null or empty list if not recurring.
        - reminders: Object with 'useDefault' (bool) and 'overrides' (list of {{"method": "popup", "minutes": X}}). 
          Example for "remind 15 min before": {{"useDefault": false, "overrides": [{{"method": "popup", "minutes": 15}}]}}.
          If no specific reminder mentioned, set "useDefault": true.

        Time Rules:
        - "Tomorrow" means +1 day from current time.
        - "Next Monday" means the coming Monday.
        - "Afternoon" usually means 14:00 (2 PM).
        - "Morning" usually means 09:00 (9 AM).
        - "Evening" usually means 18:00 (6 PM).

        Output strictly JSON. No markdown blocks.
        """
        
        try:
            # Sync call in async wrapper perfectly fine for low volume, 
            # or could use run_in_executor if needed. The SDK is sync by default usually unless async client used.
            # google.genai has async support but let's stick to standard usage unless we check async client.
            # Actually, standard Client is sync. Let's assume sync for now, wrapped in try/except.
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            # With response_mime_type="application/json", response.text should be clean JSON
            clean_text = response.text.strip()
            event_data = json.loads(clean_text)
            return event_data
            
        except Exception as e:
            logger.error(f"Gemini Error: {e}")
            return None

    async def parse_audio(self, audio_path: str, mime_type: str = "audio/ogg"):
         """Parses voice note directly into event JSON."""
         if not self.client: return None
         
         current_time = datetime.datetime.now().isoformat()
         
         try:
            # Upload file with new SDK
            # Note: config={'mime_type': ...} usage
            myfile = self.client.files.upload(path=audio_path, config={'mime_type': mime_type})
            
            prompt = f"""
            Listen to this voice note. It contains a calendar event request.
            Current time: {current_time}
            
            Extract the event details into JSON:
            {{ 
                "summary": "...", 
                "start": "ISO8601", 
                "end": "ISO8601", 
                "description": "...",
                "recurrence": ["RRULE:..."] or [],
                "reminders": {{ "useDefault": true/false, "overrides": [...] }}
            }}
            """
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[myfile, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            clean_text = response.text.strip()
            return json.loads(clean_text)
            
         except Exception as e:
             logger.error(f"Gemini Audio Error: {e}")
             return None

gemini_service = GeminiService()
