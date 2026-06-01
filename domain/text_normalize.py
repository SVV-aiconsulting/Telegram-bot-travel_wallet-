"""Нормализация текста для поиска в справочниках."""

from __future__ import annotations

import re


def normalize_lookup_text(text: str) -> str:
    """Единый вид для поиска страны или названия в справочнике."""
    t = text.strip().lower().replace("ё", "е")
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE)
    return " ".join(t.split())


def normalize_currency_code(text: str) -> str:
    """Код валюты: верхний регистр, латиница."""
    return text.strip().upper()
