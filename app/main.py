from fastapi import FastAPI, Request
from aiogram import types, Bot
from app.bot import dp, bot
from app.core import config
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    """Register webhook on startup if URL is configured."""
    webhook_url = config.settings.WEBHOOK_URL
    if webhook_url:
        webhook_endpoint = f"{webhook_url}{config.settings.WEBHOOK_PATH}"
        logger.info(f"🚀 Setting webhook to: {webhook_endpoint}")
        await bot.set_webhook(webhook_endpoint)
    else:
        logger.warning("⚠️ WEBHOOK_URL not set. Running in server mode without webhook registration.")

@app.on_event("shutdown")
async def on_shutdown():
    """Remove webhook on shutdown."""
    logger.info("🛑 Removing webhook...")
    await bot.delete_webhook()

@app.post(config.settings.WEBHOOK_PATH)
async def bot_webhook(request: Request):
    """Receive updates from Telegram."""
    update_data = await request.json()
    update = types.Update(**update_data)
    await dp.feed_update(bot, update)
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"status": "Telegram Calendar Bot is running"}
