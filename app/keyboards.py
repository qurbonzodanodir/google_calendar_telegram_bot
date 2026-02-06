from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_main_menu() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="📅 Agenda"), KeyboardButton(text="➕ New task")],
        [KeyboardButton(text="🔄 Refresh Lists")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    """
    Returns [✅ Create] [❌ Cancel] buttons.
    :param action: 'event' or 'task' (used for callback data if needed, currently generic)
    """
    buttons = [
        [
            InlineKeyboardButton(text="✅ Create", callback_data=f"confirm_{action}"),
            InlineKeyboardButton(text="❌ Cancel", callback_data=f"cancel_{action}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_project_selection_keyboard(lists: list) -> InlineKeyboardMarkup:
    """Returns inline buttons for project selection."""
    buttons = []
    for l in lists:
        btn = InlineKeyboardButton(text=l['title'], callback_data=f"list:{l['id']}")
        buttons.append([btn])
    
    buttons.append([InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_task")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
