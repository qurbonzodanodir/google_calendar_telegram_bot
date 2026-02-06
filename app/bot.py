import logging
import asyncio
from aiogram import Bot, Dispatcher
from app.core import config
from app.handlers import info, tasks, calendar, voice

# Configure logging
logging.basicConfig(level=logging.INFO)

# Compatibility for app/main.py and run.py
bot = Bot(token=config.settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Register Routers
dp.include_router(info.router)
dp.include_router(calendar.router)
dp.include_router(voice.router)
dp.include_router(tasks.router)

async def main():
    print("🤖 Bot is starting (Clean Architecture)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
