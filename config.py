"""Загрузка конфигурации приложения из переменных окружения."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


class ConfigError(Exception):
    """Ошибка конфигурации — отсутствует обязательная переменная окружения."""


@dataclass(frozen=True)
class AppConfig:
    """Настройки приложения."""

    telegram_bot_token: str
    currency_api_key: str
    database_path: str


def _require_env(name: str) -> str:
    """Читает обязательную переменную окружения или выбрасывает понятную ошибку."""
    value = os.getenv(name)
    if not value or not value.strip():
        raise ConfigError(
            f"Не задана переменная окружения {name}. "
            f"Создайте файл .env по образцу .env.example и укажите значение."
        )
    return value.strip()


def load_config() -> AppConfig:
    """
    Загружает конфигурацию из .env.

    Без TELEGRAM_BOT_TOKEN и CURRENCY_API_KEY приложение не запускается.
    """
    database_path = os.getenv("DATABASE_PATH", "travel_wallet.sqlite3").strip()
    if not database_path:
        database_path = "travel_wallet.sqlite3"

    return AppConfig(
        telegram_bot_token=_require_env("TELEGRAM_BOT_TOKEN"),
        currency_api_key=_require_env("CURRENCY_API_KEY"),
        database_path=database_path,
    )
