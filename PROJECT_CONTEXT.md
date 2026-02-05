# Project Context: Telegram Calendar Bot

**Date:** Feb 5, 2026
**Status:** 🟢 Live (Deployed on Google Cloud Run)
**Repository:** [github.com/qurbonzodanodir/google_calendar_telegram_bot](https://github.com/qurbonzodanodir/google_calendar_telegram_bot)
**Live Bot URL:** `https://google-calendar-telegram-bot-410038261083.europe-west1.run.app`

## Overview
A smart Telegram bot that manages your Google Calendar. It uses **Google Gemini** to understand natural language (text & voice) and **FastAPI** for webhooks.

## Key Features
1.  **Natural Language Parsing**: Uses **Groq** (model: `llama-3.3-70b-versatile`) to extract event details (summary, start time, end time) from user input.

    *   Supports text: "Meeting tomorrow at 10am"
    *   Supports voice: Transcribes and extracts intent from audio files.
2.  **Advanced Scheduling**:
    *   **Recurring Events**: Supports "Every Monday", "Daily", etc. (RRULE).
    *   **Custom Reminders**: Supports "Remind me 15 min before".
3.  **Google Calendar Integration**: Uses `google-api-python-client` with OAuth2.
    *   Scopes: `calendar.events` (for creating events).
    *   Auth: Reuses credentials from a local MCP server setup (`credentials.json` + `token.json`).
4.  **Productivity Focus**: The bot complements a "Prayer Time" calendar strategy where the user has 20-minute fixed blocks for prayer, and the rest of the time is for deep work. This bot removes the friction of scheduling that deep work.

## Architecture
*   **Stack**: Python 3.12, FastAPI (future webhook support), Aiogram 3 (Bot logic), Google Generative AI SDK, Google Calendar API.
*   **Location**: `/Users/nodir/Desktop/telegram-calendar-bot/`
*   **Entry Point**: `run.py` (Polling mode).

## Current Status (Feb 5, 2026)
*   ✅ Core logic (Groq + Calendar) verified via `test_services.py`.
*   ✅ **New**: Recurring events and custom reminders implemented and verified.
*   ✅ Bot is running locally in polling mode.
*   ✅ User has successfully moved the project to the Desktop.

## For Future Agents
If you are working on this project:
1.  Check `app/services/gemini.py` for prompt engineering (recurrence/reminders).
2.  Check `app/services/calendar.py` for OAuth and Event insertion logic.
3.  The `.env` file contains the API keys (not included here for security, but expected to be present).
