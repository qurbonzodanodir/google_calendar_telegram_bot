
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from app.core import config
from app.services.tasks import tasks_service

from app.services.calendar import calendar_service
from app.services.groq_service import groq_service
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=config.settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

@dp.message(F.text)
async def handle_text(message: types.Message):
    if not config.settings.GROQ_API_KEY:
        await message.answer("⚠️ Please configure GROQ_API_KEY in .env first.")
        return

    wait_msg = await message.answer("🧠 Thinking...")
    
    try:
        # 0. Fetch available task lists (so LLM knows where to put it)
        try:
            available_lists = tasks_service.get_task_lists()
        except:
             # Fallback if tasks service fails (e.g.auth issue)
            available_lists = []

        # 1. Parse with Groq
        event_data = await groq_service.parse_event(message.text, task_lists=available_lists)
        
        if not event_data:
            await wait_msg.edit_text("😕 I couldn't understand the date/time. Please try again.")
            return

        # === HANDLE TASK ===
        if event_data.get('type') == 'task':
            list_id = event_data.get('list_id', '@default')
            
            # Find list name for display
            list_name = "My Tasks"
            for l in available_lists:
                if l['id'] == list_id:
                    list_name = l['title']
                    break

            task_link = tasks_service.create_task(
                title=event_data['title'],
                notes=event_data.get('notes', ''),
                due=event_data.get('due'),
                tasklist_id=list_id
            )
            await wait_msg.edit_text(f"✅ **Task Created!**\n"
                                     f"📂 List: **{list_name}**\n"
                                     f"📝 {event_data['title']}\n"
                                     f"🔗 [Open Google Tasks]({task_link})", parse_mode="Markdown")
            return

        # === HANDLE CALENDAR EVENT ===
        # (Default to event if type is missing or 'event')
        
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
    if not config.settings.GROQ_API_KEY:
        await message.answer("⚠️ Please configure GROQ_API_KEY in .env first.")
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

        # 2. Process with Groq
        event_data = await groq_service.parse_audio(local_filename)
        
        # Cleanup file
        import os
        os.remove(local_filename)

        if not event_data:
             await wait_msg.edit_text("😕 I couldn't understand the audio.")
             return

        # === HANDLE TASK ===
        if event_data.get('type') == 'task':
            task_link = tasks_service.create_task(
                title=event_data['title'],
                notes=event_data.get('notes', ''),
                due=event_data.get('due')
            )
            await wait_msg.edit_text(f"✅ **Task Created!**\n"
                                     f"📝 {event_data['title']}\n"
                                     f"🔗 [Open Google Tasks]({task_link})", parse_mode="Markdown")
            return

        # === HANDLE EVENT ===
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
