from aiogram import Router, types
from aiogram.filters import Command
from app.keyboards import get_main_menu

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = get_main_menu()
    
    await message.answer("👋 **Hello!** I'm your AI Assistant.\n\n"
                         "Use the menu below or just type naturally:\n"
                         "• *\"Meeting with Team at 2pm\"*\n"
                         "• *\"Fix login bug\"*", 
                         reply_markup=keyboard, parse_mode="Markdown")
