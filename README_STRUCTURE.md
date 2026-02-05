
# Telegram Calendar Bot Structure

## 📂 Project Structure
```
telegram-calendar-bot/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI entry point (Webhooks & Server)
│   ├── bot.py           # Aiogram Bot Setup & Dispatcher
│   ├── core/            # Configuration & Settings
│   │   ├── __init__.py
│   │   └── config.py
│   ├── services/        # Business Logic
│   │   ├── __init__.py
│   │   ├── calendar.py  # Google Calendar Integration
│   │   └── gemini.py    # AI Logic (Gemini Pro)
│   └── handlers/        # Telegram Command Handlers
│       ├── __init__.py
│       └── common.py
├── .env                 # Secrets
├── requirements.txt     # Dependencies
└── run.py               # Dev execution script
```

## 🚀 Services
- **FastAPI**: Serves as the web server (webhook receiver).
- **Aiogram**: Handles Telegram updates asynchronously.
- **Google Calendar API**: Manages events.
- **Google Gemini API**: Parses natural language and voice.
