from groq import Groq
from app.core import config
import logging

logger = logging.getLogger(__name__)

class GroqClientWrapper:
    def __init__(self):
        self.client = None
        self.text_model = "llama-3.3-70b-versatile"
        self.audio_model = "distil-whisper-large-v3-en"
        
        if config.settings.GROQ_API_KEY:
            try:
                self.client = Groq(api_key=config.settings.GROQ_API_KEY)
                logger.info("✅ Groq Client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to init Groq Client: {e}")
        else:
            logger.warning("⚠️ GROQ API Key missing in environment settings!")

    def get_client(self):
        if not self.client:
            raise Exception("GROQ API Key is missing or invalid")
        return self.client

# Singleton instance
groq_client = GroqClientWrapper()
