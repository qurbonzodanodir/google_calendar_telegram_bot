from aiogram import Router, types, F
from app.services.tasks.service import tasks_service
from app.services.ai.service import ai_service
from app.services.calendar.service import calendar_service
from app.keyboards import get_main_menu, get_confirm_keyboard, get_project_selection_keyboard
import datetime

router = Router()

# Simple in-memory state: {user_id: {"state": str, "data": dict}}
USER_STATE = {}

@router.message(F.text == "➕ New task")
async def handle_new_task_wizard(message: types.Message):
    try:
        lists = tasks_service.get_task_lists()
        # Build Keyboard with Project Names using helper
        keyboard = get_main_menu() # Fallback? No, we need custom reply keyboard for lists.
        
        # We'll stick to dynamic generation here for ReplyKeyboard but maybe move logic if needed generic.
        # For now, let's keep it simple as ReplyKeyboard is specific here.
        kb_rows = []
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
            "lists": lists
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
    """Callback for creating a Task from AI suggestion."""
    
    data = callback_query.data
    # Use message text or caption if available
    message_text = callback_query.message.text or ""
    
    if data == "cancel_task":
        await callback_query.message.edit_text("❌ Action cancelled.")
        return

    # Extract Task Title from Message Text (brittle parsing, but fits current UX)
    task_title = "New Task"
    try:
        if "Task Detected: " in message_text:
            task_title = message_text.split("Task Detected: ")[1].split("\n")[0].strip()
        else:
            task_title = message_text.split("\n")[0]
    except:
        pass

    try:
        list_id = data.split(":", 1)[1]
    except IndexError:
        await callback_query.message.edit_text("❌ Invalid List Data")
        return
    
    await callback_query.message.edit_text(f"⏳ Saving '{task_title}'...")
    
    try:
        tasks_service.create_task(title=task_title, notes="", tasklist_id=list_id)
        await callback_query.message.edit_text(f"✅ Saved <b>{task_title}</b> to Project!", parse_mode="HTML")
    except Exception as e:
        await callback_query.message.edit_text(f"❌ Error creating task: {e}")

# --- NEW: Event Confirmation Handler ---
@router.callback_query(lambda c: c.data in ["confirm_event", "cancel_event"])
async def process_event_confirmation(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    state_info = USER_STATE.get(user_id)
    if not state_info or state_info.get("state") != "CONFIRM_EVENT":
        await callback_query.answer("⚠️ Session expired.", show_alert=True)
        await callback_query.message.delete()
        return

    if data == "cancel_event":
        del USER_STATE[user_id]
        await callback_query.message.edit_text("❌ Event cancelled.")
        return

    if data == "confirm_event":
        event_data = state_info.get("data")
        try:
            await callback_query.message.edit_text("⏳ Creating event...")
            
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
            
            del USER_STATE[user_id]
            await callback_query.message.edit_text(
                f"✅ **Event Created!**\n📅 {event_data['summary']}\n🔗 [Open in Google Calendar]({link})", 
                parse_mode="Markdown"
            )
        except Exception as e:
            await callback_query.message.edit_text(f"❌ Error: {e}")


@router.message(F.text)
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    state_info = USER_STATE.get(user_id)
    text = message.text

    # Skip commands/menus handled by other routers (sanity check)
    if text.startswith("/") or text in ["📅 Agenda", "➕ New task", "🔄 Refresh Lists", "🔙 Back"]:
        return

    # === HANDLE WIZARD STATES ===
    if state_info:
        state = state_info.get("state")
        
        if state == "CHOOSING_PROJECT":
            lists = state_info.get("lists", [])
            selected_list = next((l for l in lists if l['title'] == text), None)
            
            if selected_list:
                USER_STATE[user_id] = {
                    "state": "WAITING_FOR_TASK",
                    "list_id": selected_list['id'],
                    "list_title": selected_list['title']
                }
                kb = [[types.KeyboardButton(text="🔙 Back")]]
                keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
                await message.answer(f"📝 Enter the task for **{selected_list['title']}**:", 
                                     reply_markup=keyboard, parse_mode="Markdown")
                return
            else:
                if text == "🔙 Back": return 
                await message.answer("⚠️ Please select a project from the menu.")
                return

        elif state == "WAITING_FOR_TASK":
            list_id = state_info.get("list_id")
            list_title = state_info.get("list_title")
            
            try:
                tasks_service.create_task(title=text, notes="", tasklist_id=list_id)
                await message.answer(f"✅ Saved **{text}** to **{list_title}**!", 
                                     reply_markup=get_main_menu(), parse_mode="Markdown")
                del USER_STATE[user_id]
            except Exception as e:
                await message.answer(f"❌ Error creating task: {e}")
            return

    # === REGULAR AI LOGIC ===
    wait_msg = await message.answer("🧠 Thinking...")
    
    try:
        # Fetch lists context
        try:
            available_lists = tasks_service.get_task_lists()
        except:
            available_lists = []

        # Parse with AI Service
        event_data = await ai_service.parse_event(text, task_lists=available_lists)
        
        if not event_data:
            await wait_msg.edit_text("😕 I couldn't understand the date/time.")
            return

        # === 1. TASK ===
        if event_data.get('type') == 'task':
            keyboard = get_project_selection_keyboard(available_lists)
            await wait_msg.edit_text(
                f"📂 Task Detected: {event_data.get('title')}\n"
                f"👇 <b>Select the Project (or ignore to use default):</b>",
                reply_markup=keyboard, parse_mode="HTML"
            )
            return

        # === 2. EVENT (CONFIRMATION FLOW) ===
        # Store in state
        USER_STATE[user_id] = {
            "state": "CONFIRM_EVENT",
            "data": event_data
        }
        
        summary = event_data['summary']
        start_pretty = event_data['start'].replace('T', ' ')
        end_pretty = event_data['end'].replace('T', ' ')
        
        confirm_text = (
            f"📅 **Verify Event:**\n\n"
            f"📌 **{summary}**\n"
            f"🕒 {start_pretty}\n"
            f"🛑 {end_pretty}\n\n"
            f"Create this event?"
        )
        
        await wait_msg.edit_text(confirm_text, reply_markup=get_confirm_keyboard("event"), parse_mode="Markdown")

    except Exception as e:
        await wait_msg.edit_text(f"❌ Error: {str(e)}")
