"""Tallukkabot - Vercel serverless webhook entry point.

Deploy target: POST /api/webhook receives a Telegram update as JSON and
hands it to the shared python-telegram-bot Application from bot_core.py.
Vercel's Python runtime auto-detects the `app` ASGI instance below.
"""

from fastapi import FastAPI, Request
from telegram import Update

from bot_core import build_application

app = FastAPI()
application = build_application()
_initialized = False


@app.post("/api/webhook")
async def telegram_webhook(request: Request) -> dict:
    global _initialized
    if not _initialized:
        await application.initialize()
        _initialized = True

    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}
