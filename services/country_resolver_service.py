"""
Определение валюты по названию страны через справочник в SQLite.
"""

from __future__ import annotations

from typing import Optional

from database_layer.country_currency_database import CountryCurrencyDatabase
from domain.text_normalize import normalize_currency_code, normalize_lookup_text


class CountryResolverService:
    """Поиск валюты по стране (5 языков) или по коду ISO."""

    def __init__(self, country_currency_db: CountryCurrencyDatabase) -> None:
        self._db = country_currency_db

    def lookup_currency_by_country(self, country_text: str) -> Optional[str]:
        """Возвращает код валюты (EUR, USD, …) или None."""
        return self._db.lookup_currency_by_country_name(country_text)

    def is_valid_currency_code(self, code: str) -> bool:
        """Код из 3 латинских букв и есть в supported_currencies."""
        normalized = normalize_currency_code(code)
        if len(normalized) != 3 or not normalized.isascii() or not normalized.isalpha():
            return False
        return self._db.is_currency_supported(normalized)

    def resolve_currency_input(self, text: str) -> Optional[str]:
        """
        Распознаёт ввод: код валюты (USD) или страна на любом языке (Мальта → EUR).
        """
        stripped = text.strip()
        if not stripped:
            return None

        normalized_code = normalize_currency_code(stripped)
        if len(normalized_code) == 3 and normalized_code.isascii() and normalized_code.isalpha():
            if self._db.is_currency_supported(normalized_code):
                return normalized_code

        return self.lookup_currency_by_country(stripped)
