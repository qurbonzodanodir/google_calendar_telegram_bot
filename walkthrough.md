# Walkthrough: Recurring Events & Reminders

## Overview
We've supercharged your Telegram Bot! It can now handle complex scheduling like repeating events and custom reminders.

## 🔁 Recurring Events (Powered by Groq Llama 3)
The bot now understands when you say "every".
*   **User:** "Gym every Monday and Friday at 6pm"
*   **Bot:** Sets the event to repeat weekly on Mon & Fri.
*   **Technical:** Uses standard `RRULE` format for Google Calendar.

## ⏰ Custom Reminders
You can specify when you want to be notified.
*   **User:** "Call Mom tomorrow at 10am, remind me 15 minutes before"
*   **Bot:** Sets a specific popup reminder for 15 minutes.
*   **Default:** If you don't say anything, it uses your Google Calendar defaults.

## Verification
We verified this with `test_services.py`.
```bash
✅ Groq Advanced Response: {
  'summary': 'Weekly Status Meeting', 
  'recurrence': ['RRULE:FREQ=WEEKLY;BYDAY=MO'], 
  'reminders': {'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': 15}]}
}
✅ Advanced Event created successfully!
```

## How to use
Just talk to the bot naturally!
> "Team meeting every weekday at 9am"
> "Lunch with Ali tomorrow, remind me 1 hour before"

---

## 🚀 Deployment Guide (Google Cloud Run)
The bot is deployed on Google Cloud Run as a containerized service.

### Live Status
*   **URL:** `https://google-calendar-telegram-bot-410038261083.europe-west1.run.app`
*   **Mode:** Webhook (Hybrid Architecture)

### Configuration (Environment Variables)
These variables must be set in Cloud Run -> Edit -> Variables:
| Variable | Value |
| :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | (Your Token) |
| `GROQ_API_KEY` | (Your Key) |
| `WEBHOOK_URL` | Your Cloud Run Service URL |
| `GOOGLE_CREDENTIALS_JSON` | Content of `credentials.json` |
| `GOOGLE_TOKEN_JSON` | Content of `token.json` |

### How to Update
1.  **Commit & Push:**
    ```bash
    git add .
    git commit -m "Your changes"
    git push
    ```
2.  **Redeploy:**
    *   Go to Google Cloud Run Console.
    *   Select Service -> **"Edit & Deploy New Revision"**.
    *   Click **"Deploy"**.
