from aiogram import Router, types, F
from app.services.tasks import tasks_service
from app.services.groq_service import groq_service
from app.services.calendar import calendar_service

router = Router()

@router.message(F.text == "➕ New task")
async def handle_new_task_help(message: types.Message):
    await message.answer("To create a task, just type it!\n\n"
                         "Examples:\n"
                         "• <i>\"Buy milk\"</i>\n"
                         "• <i>\"Fix server bug tomorrow\"</i>\n"
                         "• <i>\"Call Mom at 5pm\"</i>", parse_mode="HTML")

@router.message(F.text == "🔄 Refresh Lists")
async def handle_refresh(message: types.Message):
    try:
        lists = tasks_service.get_task_lists()
        count = len(lists)
        names = ", ".join([l['title'] for l in lists])
        await message.answer(f"✅ **Lists Refreshed!**\nFound {count} lists:\n{names}", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Error: {e}")

@router.callback_query(lambda c: c.data.startswith("list:") or c.data == "cancel_task")
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
    task_title = "New Task"
    try:
        if "Task Detected: " in message_text:
            task_title = message_text.split("Task Detected: ")[1].split("\n")[0].strip()
        else:
            task_title = message_text.split("\n")[0]
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
    
    # 4. Create Task
    try:
        tasks_service.create_task(title=task_title, notes="", tasklist_id=list_id)
        await callback_query.message.edit_text(f"✅ Saved <b>{task_title}</b> to Project!", parse_mode="HTML")
    except Exception as e:
        await callback_query.message.edit_text(f"❌ Error creating task: {e}")

@router.message(F.text)
async def handle_text(message: types.Message):
    # Skip commands/menus handled by other routers
    if message.text.startswith("/") or message.text in ["📅 Agenda", "➕ New task", "🔄 Refresh Lists"]:
        return

    wait_msg = await message.answer("🧠 Thinking...")
    
    try:
        # Fetch lists for context
        try:
            available_lists = tasks_service.get_task_lists()
        except:
            available_lists = []

        # Parse with Groq
        event_data = await groq_service.parse_event(message.text, task_lists=available_lists)
        
        if not event_data:
            await wait_msg.edit_text("😕 I couldn't understand the date/time. Please try again.")
            return

        # === HANDLE TASK ===
        if event_data.get('type') == 'task':
            buttons = []
            for l in available_lists:
                btn = types.InlineKeyboardButton(text=l['title'], callback_data=f"list:{l['id']}")
                buttons.append([btn])
            buttons.append([types.InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_task")])
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
            
            await wait_msg.edit_text(
                f"📂 Task Detected: {event_data.get('title')}\n"
                f"👇 <b>Select the Project:</b>",
                reply_markup=keyboard, parse_mode="HTML"
            )
            return

        # === HANDLE CALENDAR EVENT ===
        # (Assuming event creation stays here or moves to calendar.py. 
        # Ideally, move the EVENT creation logic to calendar.py but trigger it here? 
        # For simplicity, I will keep event creation logic here for now, or just delegate.)
        
        # Let's keep event creation here for simplicity since Groq descides the type
        import datetime
        confirm_msg = f"Creating event...\n📅 **{event_data['summary']}**\n🕒 {event_data['start']} - {event_data['end']}"
        await wait_msg.edit_text(confirm_msg)

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
        await wait_msg.edit_text(f"✅ **Event Created!**\n📅 {event_data['summary']}\n🔗 [Open in Google Calendar]({link})", parse_mode="Markdown")

    except Exception as e:
        await wait_msg.edit_text(f"❌ Error: {str(e)}") 
