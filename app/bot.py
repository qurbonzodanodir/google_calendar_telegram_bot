import logging
import asyncio
from aiogram import Bot, Dispatcher
from app.core import config
from app.handlers import info, tasks, calendar, voice

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    print("🤖 Bot is starting (Refactored Architecture)...")
    
    # Initialize bot and dispatcher
    bot = Bot(token=config.settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    
    # Register Routers
    dp.include_router(info.router)
    dp.include_router(calendar.router)
    dp.include_router(voice.router)
    # Tasks router catches generic text, so register it last (or check filters carefully)
    dp.include_router(tasks.router)

    # Webhook Mode Check?
    # If running main() directly, we assume polling. 
    # If using FastAPI/Cloud Run, main.py imports 'dp' and 'bot'.
    # So we need to expose 'dp' and 'bot' globally or restructure main.py too.
    # Refactor Note: app/main.py imports 'dp' and 'bot' from app.bot.
    # To keep compatibility, we must expose them at module level.
    
    await dp.start_polling(bot)

# Compatibility for app/main.py
bot = Bot(token=config.settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
dp.include_router(info.router)
dp.include_router(calendar.router)
dp.include_router(voice.router)
dp.include_router(tasks.router)

if __name__ == "__main__":
    asyncio.run(main())
