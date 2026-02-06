from aiogram import Router, types, F
from app.services.calendar.service import calendar_service

router = Router()

@router.message(F.text == "📅 Agenda")
async def handle_agenda(message: types.Message):
    try:
        events = calendar_service.list_events(max_results=10)
        if not events:
            await message.answer("📅 No upcoming events found.")
            return

        text = "📅 **Upcoming Events:**\n\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'No Title')
            # Simple format cleanup
            clean_time = start.replace('T', ' ').split('+')[0]
            text += f"• <b>{clean_time}</b>: {summary}\n"
        
        await message.answer(text, parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Error fetching agenda: {e}")
