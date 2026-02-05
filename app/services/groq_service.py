
import json
import datetime
import os
from groq import Groq
from app.core import config
import logging

logger = logging.getLogger(__name__)

class GroqService:
    def __init__(self):
        if config.settings.GROQ_API_KEY:
            self.client = Groq(api_key=config.settings.GROQ_API_KEY)
            self.text_model = "llama-3.3-70b-versatile"
            self.audio_model = "distil-whisper-large-v3-en"
        else:
            self.client = None
            logger.warning("GROQ API Key missing!")

    async def parse_event(self, text: str, user_timezone: str = "Asia/Dushanbe"):
        """Parses natural language text into a structured JSON event using Llama 3."""
        if not self.client:
            raise Exception("GROQ API Key is missing in .env")

        current_time = datetime.datetime.now().isoformat()
        
        prompt = f"""
        You are a smart calendar assistant. 
        Current time: {current_time}
        User Timezone: {user_timezone}

        Extract the event details from the user's text: "{text}"

        Return a VALID JSON object with the following fields:
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

        IMPORTANT: Return ONLY the JSON object. Do not wrap it in markdown code blocks like ```json ... ```. Just raw JSON.
        """
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.text_model,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            
            response_content = chat_completion.choices[0].message.content
            return json.loads(response_content)
            
        except Exception as e:
            logger.error(f"Groq Text Error: {e}")
            return None

    async def parse_audio(self, audio_path: str):
         """Transcribes voice note using Whisper, then parses text."""
         if not self.client: return None
         
         try:
            # 1. Transcribe Audio
            with open(audio_path, "rb") as file:
                transcription = self.client.audio.transcriptions.create(
                    file=(os.path.basename(audio_path), file.read()),
                    model=self.audio_model,
                    response_format="json",
                    language="en", # Defaulting to en, but model handles others well or auto-detects
                    temperature=0.0
                )
            
            text = transcription.text
            logger.info(f"Groq Whisper Transcribed: {text}")
            
            # 2. Parse Text
            return await self.parse_event(text)
            
         except Exception as e:
             logger.error(f"Groq Audio Error: {e}")
             return None

groq_service = GroqService()
