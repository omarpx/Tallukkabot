"""Tallukkabot - a Finnish humor Telegram bot.

Upgraded: token loaded from the environment, cleaned-up structure,
logging, a few extra commands, optional stats, an optional daily
scheduled message, and an optional local-LLM (Ollama) fallback reply.
"""

import logging
import os
import random
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Final

import httpx  # bundled with python-telegram-bot, no extra install needed

# python-dotenv is optional; if installed it loads a local .env file.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# --------------------------------------------------------------------------
# Configuration (all secrets come from the environment, never the source)
# --------------------------------------------------------------------------

TOKEN: Final = os.environ.get("TELEGRAM_BOT_TOKEN")
USERNAME: Final = os.environ.get("BOT_USERNAME", "@tallukkabot")

# Optional local LLM (Ollama). If OLLAMA_HOST is unreachable or unset the
# bot silently falls back to the classic hardcoded default reply.
OLLAMA_HOST: Final = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL: Final = os.environ.get("OLLAMA_MODEL", "llama3.2")
USE_LLM: Final = os.environ.get("USE_LLM", "true").lower() == "true"

# Optional daily scheduled greeting. Set DAILY_CHAT_ID to the chat that
# should receive it (and DAILY_TIME as HH:MM, defaults to 12:00).
DAILY_CHAT_ID: Final = os.environ.get("DAILY_CHAT_ID")
DAILY_TIME: Final = os.environ.get("DAILY_TIME", "12:00")

STATS_FILE: Final = Path(__file__).with_name("stats.json")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("tallukkabot")

# --------------------------------------------------------------------------
# Tiny persisted stats (kept intentionally simple)
# --------------------------------------------------------------------------

import json


def load_stats() -> dict:
    try:
        return json.loads(STATS_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"messages": 0, "commands": {}}


def save_stats(stats: dict) -> None:
    try:
        STATS_FILE.write_text(json.dumps(stats), encoding="utf-8")
    except OSError as exc:
        logger.warning("Could not save stats: %s", exc)


STATS = load_stats()


def bump(key: str) -> None:
    if key == "message":
        STATS["messages"] = STATS.get("messages", 0) + 1
    else:
        STATS["commands"][key] = STATS["commands"].get(key, 0) + 1
    save_stats(STATS)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def in_between(now: time, start: time, end: time) -> bool:
    """True if `now` falls in the [start, end) window (handles midnight wrap)."""
    if start <= end:
        return start <= now < end
    return start <= now or now < end


def two_hours_from_now() -> str:
    return format(datetime.now() + timedelta(hours=2), "%H:%M")


async def llm_reply(text: str) -> str | None:
    """Ask a local Ollama model to answer in Tallukka's style.

    Returns None if the LLM is disabled or unreachable, so the caller can
    fall back to the classic hardcoded response.
    """
    if not USE_LLM:
        return None

    system_prompt = (
        "Olet Eetu, alias Tallukka: rento suomalainen chattibotti. "
        "Vastaat lyhyesti, puhekielellä ja huumorilla, kuten kaveri "
        "Telegram-chatissa. Pidä vastaukset yhden tai kahden lauseen mittaisina."
    )
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{OLLAMA_HOST}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text},
                    ],
                    "stream": False,
                },
            )
            resp.raise_for_status()
            content = resp.json().get("message", {}).get("content", "").strip()
            return content or None
    except Exception as exc:  # network error, model missing, etc.
        logger.info("LLM fallback unavailable (%s), using default reply", exc)
        return None


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bump("start")
    await update.message.reply_text("Moi mun nimi on Eetu!")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bump("help")
    await update.message.reply_text(
        "Vihtu kirjoita jotai nii voin vastata.\n"
        "Komennot: /papanviinat /issleep /roll /flip /pick /stats"
    )


PAPANVIINAT_RESPONSES = [
    "Juuh nyt ois sitä vitun PAPAN VIINAA tarjol !!! :D",
    "Papan viinaa? Sehän on aina hyvää!",
    "Papan viina, paras tapa rentoutua!",
    # saa lisätä vapasti :D
]


async def papanviinat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bump("papanviinat")
    await update.message.reply_text(random.choice(PAPANVIINAT_RESPONSES))


ISSLEEP_RESPONSES = [
    '*Tallukka is awake* \nTallukka says:"Juuh käy sellane et tääl mun luon all in bileet"',
    '*Tallukka is awake* \nTallukka says:"Juh on hereil tääl näih"',
    '*Tallukka is awake* \nTallukka says:"Aa juuh oon jus menos sin Kilttiksel"',
]


async def issleep_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bump("issleep")
    if in_between(datetime.now().time(), time(20), time(6)):
        await update.message.reply_text(
            '*Tallukka is sleeping* \nTallukka says:"Öööö E mä nuku nyh"'
        )
    else:
        await update.message.reply_text(random.choice(ISSLEEP_RESPONSES))


async def roll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/roll [max] - random number between 1 and max (default 6)."""
    bump("roll")
    top = 6
    if context.args:
        try:
            top = max(1, int(context.args[0]))
        except ValueError:
            pass
    await update.message.reply_text(f"🎲 {random.randint(1, top)}")


async def flip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bump("flip")
    await update.message.reply_text(random.choice(["Kruuna", "Klaava"]))


async def pick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/pick a b c - pick one of the given options."""
    bump("pick")
    if not context.args:
        await update.message.reply_text("Anna vaihtoehtoja: /pick kalja siideri lonkero")
        return
    await update.message.reply_text(random.choice(context.args))


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bump("stats")
    top_cmds = sorted(STATS["commands"].items(), key=lambda kv: kv[1], reverse=True)
    lines = [f"Viestejä käsitelty: {STATS.get('messages', 0)}"]
    if top_cmds:
        lines.append("Komennot:")
        lines += [f"  /{name}: {count}" for name, count in top_cmds]
    await update.message.reply_text("\n".join(lines))


# --------------------------------------------------------------------------
# Keyword responses (order matters; first match wins)
# --------------------------------------------------------------------------

GREETINGS = ["moi", "hei", "moro"]

KALJA_RESPONSES = [
    "ääääääääääh no viihtu kai pitää sit ryypätä",
    "okei hyvä juon lisää kaljaa",
]

HOMO_RESPONSES = [
    "isäs on :D",
    "no juuh :D",
    "suusex 8=======D",
    "Eih",
]

KAYKO_RESPONSES = [
    "Juuh sellane käy",
    "öööööööö EI",
    "öööööööööööööö juuuh tän voi tul",
    "vittu sä oot autisti :D",
    "JUH käyks vaik et painut vittuu :D",
]

TUPLIS_RESPONSES = [
    "Ketää tupliksel tänää?? Vetää AIIIVAN ylilaidallinen :DDD litra long iland ice teatä naamaan ja merilyniin tanssimaan :DDD flip cuppia autokannella :DDD iskelmäbaarii laulaa aikuista naista :DDDD PURKILLINE verovapaata denssii huuleen :DDD syömäkisa buffassa :DDD kolme pulloo vergiä boksereihi :DDD jouluristeilyl jatkoille :DDD huomenna päivällä klo 12 sammuu pallomereen :DD ketä imus????",
    "ööö no periaattees vois",
    "ööööööööö EI vitus 🤮🤮🤮",
]


def nih_responses() -> list[str]:
    return [
        "ÖÖÖÖÖ no emmää tiä riippuu vähä kontekstist :D",
        f"Öööö kello tulee koht {two_hours_from_now()} et oisko teijä aika lähtee koht? :D",
        "Juuuuh :D",
        # Saa lisäillä lisää Eetun heittoja :D
    ]


def kullin_pituus_reply() -> str:
    choice = random.choice(
        [f"{random.randint(1, 30)} cm", f"{random.randint(1, 12)} tuumaa"]
    )
    value = int(choice.split()[0])
    if (value < 10 and "tuumaa" not in choice) or ("tuumaa" in choice and value < 3):
        return f"se o {choice}\nhäähääää vitun millimuna :D"
    return f"se o {choice}"


def keyword_response(text: str) -> str | None:
    """Return a hardcoded reply for known keywords, else None."""
    processed = text.lower()

    if any(word in processed for word in GREETINGS):
        return "No moi!"
    if "kalja" in processed:
        return random.choice(KALJA_RESPONSES)
    if "nih" in processed:
        return random.choice(nih_responses())
    if "homo" in processed:
        return random.choice(HOMO_RESPONSES)
    if "käykö" in processed or "käyks" in processed:
        return random.choice(KAYKO_RESPONSES)
    if "tuplis" in processed or "tupliksel" in processed:
        return random.choice(TUPLIS_RESPONSES)
    if "kullin pituus" in processed or "kullin koko" in processed:
        return kullin_pituus_reply()
    return None


async def handle_response(text: str) -> str:
    """Hardcoded keyword reply, else LLM fallback, else classic default."""
    hardcoded = keyword_response(text)
    if hardcoded is not None:
        return hardcoded

    ai = await llm_reply(text)
    if ai is not None:
        return ai

    return "mee ny vittuu siit"


# --------------------------------------------------------------------------
# Message handling
# --------------------------------------------------------------------------


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    bump("message")
    message_type = update.message.chat.type
    text = update.message.text
    logger.info('User (%s) in %s: "%s"', update.message.chat.id, message_type, text)

    if message_type == "group":
        if USERNAME not in text:
            return
        text = text.replace(USERNAME, "").strip()

    response = await handle_response(text)
    logger.info("Bot: %s", response)
    await update.message.reply_text(response)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Update %s caused error %s", update, context.error)


async def daily_greeting(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=DAILY_CHAT_ID, text=random.choice(PAPANVIINAT_RESPONSES)
    )


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def main() -> None:
    if not TOKEN:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN is not set. Put it in your environment or a .env file."
        )

    logger.info("Starting bot...")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("papanviinat", papanviinat_command))
    app.add_handler(CommandHandler("issleep", issleep_command))
    app.add_handler(CommandHandler("roll", roll_command))
    app.add_handler(CommandHandler("flip", flip_command))
    app.add_handler(CommandHandler("pick", pick_command))
    app.add_handler(CommandHandler("stats", stats_command))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    # Optional daily scheduled message (requires the job-queue extra).
    if DAILY_CHAT_ID:
        if app.job_queue is None:
            logger.warning(
                "DAILY_CHAT_ID is set but JobQueue is unavailable. "
                'Install it with: pip install "python-telegram-bot[job-queue]"'
            )
        else:
            hh, mm = (int(p) for p in DAILY_TIME.split(":"))
            app.job_queue.run_daily(daily_greeting, time=time(hh, mm))
            logger.info("Scheduled daily message at %s", DAILY_TIME)

    logger.info("Polling...")
    app.run_polling(poll_interval=1)


if __name__ == "__main__":
    main()
