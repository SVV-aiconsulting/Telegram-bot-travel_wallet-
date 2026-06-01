"""
Точка входа: Telegram-бот «миникошелёк путешественника».
"""

from __future__ import annotations

import logging
import sys

import telebot

from bot.handlers import register_handlers
from config import ConfigError, load_config
from container import create_container

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Загружает конфиг, собирает зависимости и запускает polling."""
    try:
        config = load_config()
    except ConfigError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)

    container = create_container(config)
    bot = telebot.TeleBot(config.telegram_bot_token)
    register_handlers(bot, container)

    logger.info("Бот запущен. Ожидание сообщений…")
    bot.infinity_polling()


if __name__ == "__main__":
    main()
