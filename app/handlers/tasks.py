from aiogram import Router, types, F
from app.services.tasks import tasks_service
from app.services.groq_service import groq_service
from app.services.calendar import calendar_service

router = Router()

# Simple in-memory state: {user_id: {"state": str, "data": dict}}
USER_STATE = {}

def get_main_menu():
    kb = [
        [types.KeyboardButton(text="📅 Agenda"), types.KeyboardButton(text="➕ New task")],
        [types.KeyboardButton(text="🔄 Refresh Lists")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@router.message(F.text == "➕ New task")
async def handle_new_task_wizard(message: types.Message):
    try:
        lists = tasks_service.get_task_lists()
        
        # Build Keyboard with Project Names
        kb_rows = []
        # Group in pairs
        row = []
        for l in lists:
            row.append(types.KeyboardButton(text=l['title']))
            if len(row) == 2:
                kb_rows.append(row)
                row = []
        if row:
            kb_rows.append(row)
        
        kb_rows.append([types.KeyboardButton(text="🔙 Back")])
        
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb_rows, resize_keyboard=True)
        
        USER_STATE[message.from_user.id] = {
            "state": "CHOOSING_PROJECT",
            "lists": lists # Cache lists to map title -> id
        }
        
        await message.answer("📂 **Select the Project** for the new task:", reply_markup=keyboard, parse_mode="Markdown")
        
    except Exception as e:
        await message.answer(f"❌ Error fetching projects: {e}")

@router.message(F.text == "🔙 Back")
async def handle_back(message: types.Message):
    if message.from_user.id in USER_STATE:
        del USER_STATE[message.from_user.id]
    await message.answer("🔙 Menu Restored.", reply_markup=get_main_menu())

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
    user_id = message.from_user.id
    state_info = USER_STATE.get(user_id)
    text = message.text

    # Skip if command or handled elsewhere (though F.text catches everything, 
    # so we must be careful with order. But Router priority usually helps.
    # However, since this is a general handler, we check state FIRST.)
    
    if state_info:
        state = state_info.get("state")
        
        # === STATE: CHOOSING PROJECT ===
        if state == "CHOOSING_PROJECT":
            # Check if text matches a known list
            lists = state_info.get("lists", [])
            selected_list = next((l for l in lists if l['title'] == text), None)
            
            if selected_list:
                # Project found!
                USER_STATE[user_id] = {
                    "state": "WAITING_FOR_TASK",
                    "list_id": selected_list['id'],
                    "list_title": selected_list['title']
                }
                
                # Show "Cancel" or "Back" keyboard? Or just generic
                kb = [[types.KeyboardButton(text="🔙 Back")]]
                keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
                
                await message.answer(f"📝 Enter the task for **{selected_list['title']}**:", 
                                     reply_markup=keyboard, parse_mode="Markdown")
                return
            else:
                # Validation error? Or maybe user clicked a command?
                if text == "🔙 Back":
                    # Handled by separate handler above, but just in case
                    return 
                await message.answer("⚠️ Please select a project from the menu.")
                return

        # === STATE: WAITING FOR TASK ===
        elif state == "WAITING_FOR_TASK":
            list_id = state_info.get("list_id")
            list_title = state_info.get("list_title")
            
            # Create Task
            try:
                tasks_service.create_task(title=text, notes="", tasklist_id=list_id)
                await message.answer(f"✅ Saved **{text}** to **{list_title}**!", 
                                     reply_markup=get_main_menu(), parse_mode="Markdown")
                # Clear state
                del USER_STATE[user_id]
            except Exception as e:
                await message.answer(f"❌ Error creating task: {e}")
            return

    # === NO STATE (Regular AI Logic) ===
    # Skip commands/menus handled by other routers
    if text.startswith("/") or text in ["📅 Agenda", "➕ New task", "🔄 Refresh Lists", "🔙 Back"]:
        return

    wait_msg = await message.answer("🧠 Thinking...")
    
    try:
        # Fetch lists for context
        try:
            available_lists = tasks_service.get_task_lists()
        except:
            available_lists = []

        # Parse with Groq
        event_data = await groq_service.parse_event(text, task_lists=available_lists)
        
        if not event_data:
            await wait_msg.edit_text("😕 I couldn't understand the date/time.")
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
                f"👇 <b>Select the Project (or ignore to use default):</b>",
                reply_markup=keyboard, parse_mode="HTML"
            )
            return

        # === HANDLE CALENDAR EVENT ===
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
