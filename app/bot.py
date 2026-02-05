
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from app.core import config
from app.services.calendar import calendar_service
from app.services.gemini import gemini_service
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=config.settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("👋 Salom! I'm your AI Calendar Bot.\n\n"
                         "🎙 **Send me a voice message** or ✍️ **text**.\n"
                         "Example: 'Book a meeting with Nodir tomorrow at 10 AM'\n"
                         "Example: 'Gym on Friday evening'")

@dp.message(F.text)
async def handle_text(message: types.Message):
    if not config.settings.GEMINI_API_KEY:
        await message.answer("⚠️ Please configure GEMINI_API_KEY in .env first.")
        return

    wait_msg = await message.answer("🧠 Thinking...")
    
    try:
        # 1. Parse with Gemini
        event_data = await gemini_service.parse_event(message.text)
        
        if not event_data:
            await wait_msg.edit_text("😕 I couldn't understand the date/time. Please try again.")
            return

        # 2. visual confirmation
        confirm_msg = f"Creating event...\n📅 **{event_data['summary']}**\n🕒 {event_data['start']} - {event_data['end']}"
        
        if event_data.get('recurrence'):
            confirm_msg += f"\n🔁 Recurring: {event_data['recurrence'][0]}"
        if event_data.get('reminders') and not event_data['reminders'].get('useDefault'):
            confirm_msg += f"\n⏰ Reminder: Custom"

        await wait_msg.edit_text(confirm_msg)

        # 3. Add to Calendar
        start_dt = datetime.datetime.fromisoformat(event_data['start'])
        end_dt = datetime.datetime.fromisoformat(event_data['end'])

        link = calendar_service.create_event(
            summary=event_data['summary'],
            start_time=start_dt,
            end_time=end_dt,
            description=event_data.get('description', ''),
            recurrence=event_data.get('recurrence'),
            reminders=event_data.get('reminders')
        )
        
        await wait_msg.edit_text(f"✅ **Event Created!**\n"
                                 f"📅 {event_data['summary']}\n"
                                 f"🔗 [Open in Google Calendar]({link})", parse_mode="Markdown")

    except Exception as e:
        await wait_msg.edit_text(f"❌ Error: {str(e)}")


@dp.message(F.voice)
async def handle_voice(message: types.Message):
    if not config.settings.GEMINI_API_KEY:
        await message.answer("⚠️ Please configure GEMINI_API_KEY in .env first.")
        return

    wait_msg = await message.answer("👂 Listening & Thinking...")

    try:
        # 1. Download voice file
        file_id = message.voice.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        
        # Save locally
        local_filename = f"voice_{message.message_id}.ogg"
        await bot.download_file(file_path, local_filename)

        # 2. Process with Gemini
        event_data = await gemini_service.parse_audio(local_filename)
        
        # Cleanup file
        import os
        os.remove(local_filename)

        if not event_data:
             await wait_msg.edit_text("😕 I couldn't understand the audio.")
             return

        # 3. Create Event
        start_dt = datetime.datetime.fromisoformat(event_data['start'])
        end_dt = datetime.datetime.fromisoformat(event_data['end'])
        
        confirm_msg = f"Creating event...\n📅 **{event_data['summary']}**\n🕒 {event_data['start']}"
        if event_data.get('recurrence'):
             confirm_msg += f"\n🔁 Recurring: {event_data['recurrence'][0]}"
        
        await wait_msg.edit_text(confirm_msg)

        link = calendar_service.create_event(
            summary=event_data['summary'],
            start_time=start_dt,
            end_time=end_dt,
            description=event_data.get('description', '') + "\n(Created via Voice)",
            recurrence=event_data.get('recurrence'),
            reminders=event_data.get('reminders')
        )
        
        await wait_msg.edit_text(f"✅ **Event Created!**\n"
                                 f"📅 {event_data['summary']}\n"
                                 f"🔗 [Open in Google Calendar]({link})", parse_mode="Markdown")
                                 
    except Exception as e:
        await wait_msg.edit_text(f"❌ Error: {str(e)}")

async def main():
    print("🤖 Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
