# 🤖 AI Telegram Calendar Bot

A smart Telegram bot that manages your **Google Calendar** and **Google Tasks** using **Groq (Llama 3)** for natural language understanding.

## 🚀 Features

### 1. 🗓 Smart Scheduling (Events)
*   **What:** Meetings, appointments, time-bound activities.
*   **Trigger:** When you specify a time/duration.
*   **Example:** "Meeting with team tomorrow at 10 AM"
*   **Action:** Creates a Google Calendar Event.

### 2. ✅ Smart To-Do (Tasks)
*   **What:** Chores, reminders, quick actions.
*   **Trigger:** Action verbs without specific duration.
*   **Example:** "Buy milk", "Call Mom tonight"
*   **Action:** Creates a Google Task.

### 3. 🎙 Voice Control
*   Send a voice message, and the bot will transcribe and process it automatically!

### 4. 🧠 Powered by Llama 3
*   Understands context (e.g., "Next Monday", "Tonight", "Gym on Friday").

## 🛠 Setup & Deployment

1.  **Environment Variables**:
    *   `TELEGRAM_BOT_TOKEN`: Your BotFather token.
    *   `GROQ_API_KEY`: API Key from Groq Cloud.
    *   `GOOGLE_CREDENTIALS_JSON`: Service account or client credentials.
    *   `GOOGLE_TOKEN_JSON`: Authorized user token (created via `auth_refresh.py`).

2.  **Local Run**:
    ```bash
    pip install -r requirements.txt
    python3 run.py
    ```

3.  **Cloud Run**:
    *   Deploy passing the env vars above.
    *   **Important**: If you re-authenticate locally, update `GOOGLE_TOKEN_JSON` in Cloud Run.

## 🔧 Project Structure
*   `app/bot.py`: Main Telegram bot logic (Startup & Routing).
*   `app/handlers/`:
    *   `tasks.py`: Confirmation logic & AI handling.
    *   `calendar.py`, `voice.py`, `info.py`: Feature handlers.
*   `app/services/`:
    *   `ai/`: Groq + Whisper logic.
    *   `calendar/`: Google Calendar wrapper.
    *   `tasks/`: Google Tasks wrapper.
*   `scripts/`: Automation scripts (Knowledge Sync, etc.).

## 🤖 AI Agent & Knowledge Sync

### 1. 🧠 Update Knowledge Base (Sync)
Run this command when you change code, so the Agent and NotebookLM know about updates:
```bash
# Sync Telegram Bot code
python3 scripts/sync_knowledge.py --project telegram-bot

# Sync FinLivo Backend code
python3 scripts/sync_knowledge.py --project finlivo
```
*This generates a fresh dump in `knowledge_dumps/`.*

### 2. ⚡️ Run FinLivo Agent
To start the autonomous coding agent that watches your Google Tasks:
```bash
python3 agents/start_finlivo.py
```
*The agent will start watching the "FinLivo" task list.*
