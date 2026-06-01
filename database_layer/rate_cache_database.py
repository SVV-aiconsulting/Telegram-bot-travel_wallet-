"""Слой доступа к кэшу курсов валют."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from database import SQLiteDatabaseManager
from domain.models import RateCacheEntry


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _row_to_entry(row) -> RateCacheEntry:
    return RateCacheEntry(
        id=row["id"],
        from_currency=row["from_currency"],
        to_currency=row["to_currency"],
        rate=float(row["rate"]),
        updated_at=row["updated_at"],
    )


class RateCacheDatabase:
    """CRUD для таблицы rate_cache."""

    def __init__(self, db: SQLiteDatabaseManager) -> None:
        self._db = db

    def get_rate(self, from_currency: str, to_currency: str) -> Optional[RateCacheEntry]:
        row = self._db.select_one(
            """
            SELECT * FROM rate_cache
            WHERE from_currency = ? AND to_currency = ?
            """,
            (from_currency.upper(), to_currency.upper()),
        )
        return _row_to_entry(row) if row else None

    def upsert_rate(self, from_currency: str, to_currency: str, rate: float) -> RateCacheEntry:
        """Сохраняет или обновляет курс в кэше."""
        fc = from_currency.upper()
        tc = to_currency.upper()
        now = _now_iso()
        existing = self.get_rate(fc, tc)
        if existing:
            self._db.update(
                "rate_cache",
                {"rate": rate, "updated_at": now},
                "from_currency = ? AND to_currency = ?",
                (fc, tc),
            )
            entry = self.get_rate(fc, tc)
            assert entry is not None
            return entry

        self._db.insert(
            "rate_cache",
            {
                "from_currency": fc,
                "to_currency": tc,
                "rate": rate,
                "updated_at": now,
            },
        )
        entry = self.get_rate(fc, tc)
        assert entry is not None
        return entry
