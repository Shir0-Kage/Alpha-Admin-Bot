"""Entry point: set up the database if needed, then run the bot."""

import logging
import os

from config import validate_config, setup_logging, DB_PATH
import init_db

log = logging.getLogger(__name__)


def ensure_db():
    # init_db is idempotent, so this is safe on every start
    existed = os.path.exists(DB_PATH)
    init_db.init_db(DB_PATH, seed_groups=True)
    if not existed:
        log.info("created new database at %s", DB_PATH)


def main():
    setup_logging()
    validate_config()
    ensure_db()
    # imported after config is validated so a missing token fails clearly first
    import task_telebot  # noqa: F401  (registers the handlers)
    from telegrambot import bot

    log.info("starting bot")
    bot.infinity_polling()


if __name__ == "__main__":
    main()
