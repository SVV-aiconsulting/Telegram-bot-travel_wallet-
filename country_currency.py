"""
Обратная совместимость: функции нормализации и поиска.

Основной справочник — в SQLite (см. CountryResolverService).
"""

from __future__ import annotations

from domain.text_normalize import normalize_currency_code, normalize_lookup_text

# Алиасы для старого кода
normalize_country_input = normalize_lookup_text


def lookup_currency_by_country(country_text: str):
    """Устарело: используйте CountryResolverService через container."""
    raise RuntimeError(
        "lookup_currency_by_country устарела. "
        "Используйте container.country_resolver.lookup_currency_by_country()"
    )


def resolve_currency_input(text: str):
    raise RuntimeError("Используйте CountryResolverService.resolve_currency_input()")


def is_valid_currency_code_format(code: str) -> bool:
    normalized = normalize_currency_code(code)
    return len(normalized) == 3 and normalized.isascii() and normalized.isalpha()
