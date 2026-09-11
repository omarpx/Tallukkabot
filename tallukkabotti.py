"""Tallukkabot - local/dev polling entry point.

Shared bot logic (persona, commands, keyword replies) lives in
bot_core.py. The Vercel serverless webhook entry point is api/webhook.py -
both build the same Application via bot_core.build_application().
"""

from datetime import time

from bot_core import DAILY_CHAT_ID, DAILY_TIME, build_application, daily_greeting, logger


def main() -> None:
    try:
        app = build_application()
    except RuntimeError as exc:
        raise SystemExit(str(exc))

    logger.info("Starting bot (polling mode)...")

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
