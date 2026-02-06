from aiogram import Router, types, F, Bot
from app.core import config
from app.services.ai.service import ai_service
from app.services.tasks.service import tasks_service
from app.services.calendar.service import calendar_service
import os
import datetime

router = Router()

@router.message(F.voice)
async def handle_voice(message: types.Message, bot: Bot):
    if not config.settings.GROQ_API_KEY:
        await message.answer("⚠️ Please configure GROQ_API_KEY in .env first.")
        return

    wait_msg = await message.answer("👂 Listening & Thinking...")

    try:
        # 1. Download voice file
        file_id = message.voice.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        
        local_filename = f"voice_{message.message_id}.ogg"
        await bot.download_file(file_path, local_filename)

        # 2. Process with AI Service
        event_data = await ai_service.parse_audio(local_filename)
        
        os.remove(local_filename)

        if not event_data:
             await wait_msg.edit_text("😕 I couldn't understand the audio.")
             return

        # === HANDLE TASK ===
        if event_data.get('type') == 'task':
            # Create directly for now, or we could use the UI flow?
            # Let's keep voice simple: Auto-create in default list for now, 
            # OR ask the user? Best to ask.
            # But callback logic needs message text.
            # For iteration 1, let's just create in Default to be fast.
            task_link = tasks_service.create_task(
                title=event_data['title'],
                notes=event_data.get('notes', ''),
                due=event_data.get('due')
            )
            await wait_msg.edit_text(f"✅ **Task Created!**\n"
                                     f"📝 {event_data['title']}\n"
                                     f"🔗 [Open Google Tasks]({task_link})", parse_mode="Markdown")
            return

        # === HANDLE CALENDAR (Existing Copy-Paste Logic) ===
        start_dt = datetime.datetime.fromisoformat(event_data['start'])
        end_dt = datetime.datetime.fromisoformat(event_data['end'])
        
        link = calendar_service.create_event(
            summary=event_data['summary'],
            start_time=start_dt,
            end_time=end_dt,
            description=event_data.get('description', '') + "\n(Created via Voice)"
        )
        
        await wait_msg.edit_text(f"✅ **Event Created!**\n"
                                 f"📅 {event_data['summary']}\n"
                                 f"🔗 [Open in Google Calendar]({link})", parse_mode="Markdown")
                                 
    except Exception as e:
        await wait_msg.edit_text(f"❌ Error: {str(e)}")
