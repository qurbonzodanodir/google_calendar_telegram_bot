
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
        You are a smart calendar and tasks assistant. 
        Current time: {current_time}
        User Timezone: {user_timezone}

        Extract the intent from the user's text: "{text}"

        Determine if this is a CALENDAR EVENT (happens at a specific time, like a meeting) or a TASK (something to do, like "buy milk", usually without a specific duration).

        Return a VALID JSON object.

        ### Option 1: It is an EVENT
        {{
            "type": "event",
            "summary": "Short title",
            "start": "ISO 8601 (YYYY-MM-DDTHH:MM:SS)",
            "end": "ISO 8601",
            "description": "Details",
            "recurrence": ["RRULE..."] or [],
            "reminders": {{ "useDefault": false, "overrides": [...] }}
        }}

        ### Option 2: It is a TASK
        {{
            "type": "task",
            "title": "Short title (e.g. Buy Milk)",
            "notes": "Any extra details",
            "due": "ISO 8601 (YYYY-MM-DDTHH:MM:SS) Optional. If user says 'tomorrow', set to tomorrow morning."
        }}

        Time Rules:
        - "Tomorrow" means +1 day.
        - "Evening" = 18:00.
        
        Output strictly JSON.
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
