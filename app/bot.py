
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

# Simple in-memory state storage: {user_id: task_data_dict}
PENDING_TASKS = {}

@dp.callback_query(lambda c: c.data.startswith("list:") or c.data == "cancel_task")
async def process_project_selection(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    if data == "cancel_task":
        if user_id in PENDING_TASKS:
            del PENDING_TASKS[user_id]
        await callback_query.message.edit_text("❌ Task creation cancelled.")
        return

    # Extract list_id
    try:
        list_id = data.split(":", 1)[1]
    except IndexError:
        await callback_query.answer("Invalid Data")
        return
    
    # Retrieve pending task info
    task_info = PENDING_TASKS.get(user_id)
    
    if not task_info:
        await callback_query.message.edit_text("⚠️ Session expired. Please send the task again.")
        return
    
    await callback_query.message.edit_text("⏳ Saving...")
    
    # Create Task
    try:
        tasks_service.create_task(
            title=task_info.get("title"),
            notes=task_info.get("notes"),
            due=task_info.get("due"),
            tasklist_id=list_id
        )
        
        # Clean up state
        del PENDING_TASKS[user_id]
        
        # Determine list name again for confirmation
        # (We assume list exists since ID came from button)
        await callback_query.message.edit_text(f"✅ Saved to Project!", parse_mode="HTML")
        
    except Exception as e:
        await callback_query.message.edit_text(f"❌ Error creating task: {e}")

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
            # === INTERACTIVE ROUTING ===
            # Instead of auto-creating, we ask the user which project.
            
            # Save task data to PENDING_TASKS
            user_id = message.from_user.id
            PENDING_TASKS[user_id] = event_data
            
            # Build Buttons
            buttons = []
            for l in available_lists:
                # callback_data: "list:<list_id>"
                btn = types.InlineKeyboardButton(text=l['title'], callback_data=f"list:{l['id']}")
                buttons.append([btn])
            
            # Cancel Button
            buttons.append([types.InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_task")])
            
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
            
            await wait_msg.edit_text(
                f"📂 <b>Task Detected:</b> {event_data.get('title')}\n"
                f"👇 <b>Select the Project:</b>",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
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
