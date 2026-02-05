
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

    async def parse_event(self, text: str, user_timezone: str = "Asia/Dushanbe", task_lists: list = None):
        """
        Parses natural language text into a structured JSON event using Llama 3.
        :param task_lists: Optional list of dicts [{'id': '...', 'title': '...'}, ...]
        """
        if not self.client:
            raise Exception("GROQ API Key is missing in .env")

        current_time = datetime.datetime.now().isoformat()
        
        # Format task lists for the prompt
        lists_prompt = ""
        if task_lists:
            lists_prompt = "Available Task Lists and their likely topics:\n"
            for l in task_lists:
                # Add some "smart" context inference here (hardcoded for now, or dynamic later)
                extra_context = ""
                title_lower = l['title'].lower()
                if "finlivo" in title_lower:
                    extra_context = "(Keywords: backend, api, database, auth, python, server, livo, code)"
                elif "finapp" in title_lower:
                     extra_context = "(Keywords: frontend, app, ui, client, general)"
                elif "sms" in title_lower:
                    extra_context = "(Keywords: message, gateway, tcell, distribution)"
                
                lists_prompt += f"- ID: '{l['id']}', Name: '{l['title']}' {extra_context}\n"
            
            lists_prompt += "\nIf 'type' is 'task':\n"
            lists_prompt += "1. Analyze the text for project-specific keywords (e.g. 'api' -> FinLivo).\n"
            lists_prompt += "2. You MUST choose the most relevant 'list_id' from above based on context, even if the user didn't say the exact list name.\n"
            lists_prompt += "3. If strictly personal or unclear, use '@default'."
        
        prompt = f"""
        You are a smart calendar and tasks assistant. 
        Current time: {current_time}
        User Timezone: {user_timezone}
        
        {lists_prompt}

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
            "due": "ISO 8601 (YYYY-MM-DDTHH:MM:SS) Optional. If user says 'tomorrow', set to tomorrow morning.",
            "list_id": "ID of the list (or '@default')"
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
