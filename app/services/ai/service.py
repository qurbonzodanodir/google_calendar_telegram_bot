import json
import logging
import os
from app.services.ai.client import groq_client
from app.services.ai.prompts import PromptManager

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.wrapper = groq_client

    async def parse_event(self, text: str, user_timezone: str = "Asia/Dushanbe", task_lists: list = None):
        """
        Parses text into JSON Event/Task using Groq.
        """
        try:
            client = self.wrapper.get_client()
            prompt = PromptManager.generate_system_prompt(text, user_timezone, task_lists)
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.wrapper.text_model,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            
            response_content = chat_completion.choices[0].message.content
            return json.loads(response_content)
            
        except Exception as e:
            logger.error(f"Groq Text Parsing Error: {e}")
            return None

    async def parse_audio(self, audio_path: str):
         """Transcribes voice note using Whisper, then parses text."""
         
         try:
            client = self.wrapper.get_client()
            
            # 1. Transcribe
            with open(audio_path, "rb") as file:
                transcription = client.audio.transcriptions.create(
                    file=(os.path.basename(audio_path), file.read()),
                    model=self.wrapper.audio_model,
                    response_format="json",
                    language="en", 
                    temperature=0.0
                )
            
            text = transcription.text
            logger.info(f"Groq Whisper Transcribed: {text}")
            
            # 2. Parse Intent
            if text:
                return await self.parse_event(text)
            return None
            
         except Exception as e:
             logger.error(f"Groq Audio Error: {e}")
             return None

# Singleton instance
ai_service = AIService()
