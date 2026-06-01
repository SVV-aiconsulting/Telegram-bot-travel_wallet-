"""
Слой доступа к справочнику «страна → валюта».

Валюты синхронизируются с exchangerate.host; названия стран — на 5 языках.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from database import SQLiteDatabaseManager
from domain.text_normalize import normalize_lookup_text


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


class CountryCurrencyDatabase:
    """CRUD и поиск по справочнику country_currency_names."""

    def __init__(self, db: SQLiteDatabaseManager) -> None:
        self._db = db

    def count_country_names(self) -> int:
        row = self._db.select_one("SELECT COUNT(*) AS c FROM country_currency_names")
        return int(row["c"]) if row else 0

    def count_supported_currencies(self) -> int:
        row = self._db.select_one("SELECT COUNT(*) AS c FROM supported_currencies")
        return int(row["c"]) if row else 0

    def upsert_supported_currency(self, code: str, source: str = "api") -> None:
        code = code.upper()
        existing = self._db.select_one(
            "SELECT code FROM supported_currencies WHERE code = ?",
            (code,),
        )
        now = _now_iso()
        if existing:
            self._db.update(
                "supported_currencies",
                {"source": source, "updated_at": now},
                "code = ?",
                (code,),
            )
        else:
            self._db.insert(
                "supported_currencies",
                {"code": code, "source": source, "updated_at": now},
            )

    def is_currency_supported(self, code: str) -> bool:
        row = self._db.select_one(
            "SELECT 1 FROM supported_currencies WHERE code = ? LIMIT 1",
            (code.upper(),),
        )
        return row is not None

    def add_country_name(
        self,
        currency_code: str,
        country_name: str,
        language_code: str,
    ) -> None:
        """Добавляет название страны, если его ещё нет (без дубликатов по normalized)."""
        currency_code = currency_code.upper()
        normalized = normalize_lookup_text(country_name)
        if not normalized:
            return

        if not self.is_currency_supported(currency_code):
            self.upsert_supported_currency(currency_code, source="seed")

        exists = self._db.select_one(
            "SELECT 1 FROM country_currency_names WHERE name_normalized = ? LIMIT 1",
            (normalized,),
        )
        if exists:
            return

        self._db.insert(
            "country_currency_names",
            {
                "currency_code": currency_code,
                "country_name": country_name.strip(),
                "name_normalized": normalized,
                "language_code": language_code.lower(),
            },
        )

    def lookup_currency_by_country_name(self, country_text: str) -> Optional[str]:
        """Ищет код валюты по названию страны на любом языке из справочника."""
        key = normalize_lookup_text(country_text)
        if not key:
            return None
        row = self._db.select_one(
            """
            SELECT currency_code FROM country_currency_names
            WHERE name_normalized = ?
            LIMIT 1
            """,
            (key,),
        )
        return row["currency_code"] if row else None

    def list_supported_currency_codes(self) -> List[str]:
        rows = self._db.select_all(
            "SELECT code FROM supported_currencies ORDER BY code"
        )
        return [r["code"] for r in rows]
