
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_BOT_TOKEN: str
    GOOGLE_CREDENTIALS_PATH: str = "credentials.json"
    GOOGLE_TOKEN_PATH: str = "token.json"
    
    # Cloud Deployment (Inject JSON content directly)
    GOOGLE_CREDENTIALS_JSON: str | None = None
    GOOGLE_TOKEN_JSON: str | None = None
    
    GEMINI_API_KEY: str | None = None
    
    # Webhook Settings
    WEBHOOK_URL: str | None = None
    WEBHOOK_PATH: str = "/webhook"
    WEBHOOK_HOST: str = "0.0.0.0"
    WEBHOOK_PORT: int = 8080

    class Config:
        env_file = ".env"

settings = Settings()
