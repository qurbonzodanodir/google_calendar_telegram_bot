
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

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("👋 Hi! I'm your AI Task Manager.\n"
                         "Tell me what to do, e.g., 'Fix login bug' or 'Meeting tomorrow at 10am'.")

@dp.callback_query(lambda c: c.data.startswith("list:") or c.data == "cancel_task")
async def process_project_selection(callback_query: types.CallbackQuery):
    print(f"🔹 CALLBACK RECEIVED: {callback_query.data}")
    await callback_query.answer("Processing...")
    
    data = callback_query.data
    message_text = callback_query.message.text or callback_query.message.caption
    
    # 1. Handle Cancel
    if data == "cancel_task":
        await callback_query.message.edit_text("❌ Task creation cancelled.")
        return

    # 2. Extract Task Title from Message Text
    # Format: "📂 Task Detected: [Title]\n👇 Select..."
    task_title = "New Task"
    try:
        # Simple extraction between "Detected: " and "\n"
        if "Task Detected: " in message_text:
            task_title = message_text.split("Task Detected: ")[1].split("\n")[0].strip()
        else:
            task_title = message_text.split("\n")[0] # Fallback
    except Exception as e:
        print(f"⚠️ parsing error: {e}")
        task_title = "Untitled Task"

    # 3. Extract List ID
    try:
        list_id = data.split(":", 1)[1]
    except IndexError:
        await callback_query.message.edit_text("❌ Invalid List Data")
        return
    
    await callback_query.message.edit_text(f"⏳ Saving '{task_title}'...")
    
    # 4. Create Task (Stateless!)
    try:
        tasks_service.create_task(
            title=task_title,
            notes="", # We lose notes in this stateless approach, but Title is 90% of value. 
                      # Future: could encode notes in invisible char or DB.
            tasklist_id=list_id
        )
        await callback_query.message.edit_text(f"✅ Saved <b>{task_title}</b> to Project!", parse_mode="HTML")
        
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
            # Stateless: We embed info in the message text.
            
            # Build Buttons
            buttons = []
            for l in available_lists:
                # callback_data: "list:<list_id>"
                btn = types.InlineKeyboardButton(text=l['title'], callback_data=f"list:{l['id']}")
                buttons.append([btn])
            
            # Cancel Button
            buttons.append([types.InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_task")])
            
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
            
            # We strictly format the message so callback can parse it
            await wait_msg.edit_text(
                f"📂 Task Detected: {event_data.get('title')}\n"
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
