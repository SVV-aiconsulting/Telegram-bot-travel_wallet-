"""
Заполнение справочника стран и валют при первом запуске.

1. Коды валют — с https://api.exchangerate.host/list (если доступен API-ключ).
2. Названия стран — из data/country_names_seed.py (5 языков, в т.ч. все страны EUR).
"""

from __future__ import annotations

import logging

from currency_manager import ExchangeRateClient
from database import SQLiteDatabaseManager
from database_layer.country_currency_database import CountryCurrencyDatabase
from database_layer.reference_schema import init_reference_schema
from data.country_names_seed import COUNTRY_ENTRIES

logger = logging.getLogger(__name__)

# Резерв, если /list недоступен
FALLBACK_CURRENCY_CODES = sorted(
    {entry["currency"] for entry in COUNTRY_ENTRIES}
)


def _sync_supported_currencies(ref_db: CountryCurrencyDatabase, api_key: str | None) -> None:
    """Загружает поддерживаемые валюты с exchangerate.host."""
    codes: list[str] = []
    if api_key:
        try:
            client = ExchangeRateClient(api_key)
            codes = client.fetch_supported_currency_codes()
            logger.info("Получено %s валют с API /list", len(codes))
        except Exception as exc:
            logger.warning("Не удалось загрузить /list: %s. Используем резервный список.", exc)

    if not codes:
        codes = FALLBACK_CURRENCY_CODES
        source = "fallback"
    else:
        source = "api"

    for code in codes:
        ref_db.upsert_supported_currency(code, source=source)

    # Валюты из статического справочника стран (если API их не вернул)
    for code in FALLBACK_CURRENCY_CODES:
        ref_db.upsert_supported_currency(code, source="seed")


def _load_country_names(ref_db: CountryCurrencyDatabase) -> None:
    """Заполняет country_currency_names из статического набора."""
    added = 0
    for entry in COUNTRY_ENTRIES:
        currency = entry["currency"]
        if not ref_db.is_currency_supported(currency):
            ref_db.upsert_supported_currency(currency, source="seed")
        for lang, names in entry["names"].items():
            for name in names:
                before = ref_db.count_country_names()
                ref_db.add_country_name(currency, name, lang)
                if ref_db.count_country_names() > before:
                    added += 1
    logger.info("Справочник стран: добавлено %s названий (всего %s)", added, ref_db.count_country_names())


def ensure_country_currency_reference(
    db: SQLiteDatabaseManager,
    api_key: str | None,
    *,
    force_reseed: bool = False,
) -> None:
    """
    Создаёт таблицы справочника и заполняет их при первом запуске.

    Args:
        db: Менеджер SQLite.
        api_key: Ключ exchangerate.host для /list.
        force_reseed: Пересоздать названия стран (для скрипта обновления).
    """
    init_reference_schema(db)
    ref_db = CountryCurrencyDatabase(db)

    if ref_db.count_supported_currencies() == 0:
        _sync_supported_currencies(ref_db, api_key)

    if ref_db.count_country_names() == 0 or force_reseed:
        if force_reseed and ref_db.count_country_names() > 0:
            db.execute("DELETE FROM country_currency_names")
            logger.info("Справочник стран очищен для перезаполнения")
        _load_country_names(ref_db)
