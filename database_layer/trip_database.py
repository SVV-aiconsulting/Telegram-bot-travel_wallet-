"""Слой доступа к данным путешествий."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from database import SQLiteDatabaseManager
from domain.models import Trip


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _row_to_trip(row) -> Trip:
    return Trip(
        id=row["id"],
        telegram_user_id=row["telegram_user_id"],
        title=row["title"],
        home_country=row["home_country"],
        destination_country=row["destination_country"],
        home_currency=row["home_currency"],
        destination_currency=row["destination_currency"],
        rate=float(row["rate"]),
        rate_source=row["rate_source"],
        balance_home=float(row["balance_home"]),
        balance_destination=float(row["balance_destination"]),
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class TripDatabase:
    """CRUD для таблицы trips."""

    def __init__(self, db: SQLiteDatabaseManager) -> None:
        self._db = db

    def create_trip(
        self,
        telegram_user_id: int,
        title: str,
        home_country: Optional[str],
        destination_country: Optional[str],
        home_currency: str,
        destination_currency: str,
        rate: float,
        rate_source: str,
        balance_home: float,
        balance_destination: float,
        set_active: bool = True,
    ) -> Trip:
        """Создаёт путешествие и при необходимости делает его активным."""
        now = _now_iso()
        if set_active:
            self._deactivate_all_for_user(telegram_user_id)

        trip_id = self._db.insert(
            "trips",
            {
                "telegram_user_id": telegram_user_id,
                "title": title,
                "home_country": home_country,
                "destination_country": destination_country,
                "home_currency": home_currency,
                "destination_currency": destination_currency,
                "rate": rate,
                "rate_source": rate_source,
                "balance_home": balance_home,
                "balance_destination": balance_destination,
                "is_active": 1 if set_active else 0,
                "created_at": now,
                "updated_at": now,
            },
        )
        trip = self.get_by_id(trip_id)
        assert trip is not None
        return trip

    def get_by_id(self, trip_id: int) -> Optional[Trip]:
        row = self._db.select_one("SELECT * FROM trips WHERE id = ?", (trip_id,))
        return _row_to_trip(row) if row else None

    def get_by_id_for_user(self, trip_id: int, telegram_user_id: int) -> Optional[Trip]:
        row = self._db.select_one(
            "SELECT * FROM trips WHERE id = ? AND telegram_user_id = ?",
            (trip_id, telegram_user_id),
        )
        return _row_to_trip(row) if row else None

    def list_by_user(self, telegram_user_id: int) -> List[Trip]:
        rows = self._db.select_all(
            "SELECT * FROM trips WHERE telegram_user_id = ? ORDER BY is_active DESC, updated_at DESC",
            (telegram_user_id,),
        )
        return [_row_to_trip(r) for r in rows]

    def get_active_trip(self, telegram_user_id: int) -> Optional[Trip]:
        row = self._db.select_one(
            "SELECT * FROM trips WHERE telegram_user_id = ? AND is_active = 1 LIMIT 1",
            (telegram_user_id,),
        )
        return _row_to_trip(row) if row else None

    def set_active_trip(self, telegram_user_id: int, trip_id: int) -> Optional[Trip]:
        """Делает путешествие активным для пользователя."""
        trip = self.get_by_id_for_user(trip_id, telegram_user_id)
        if trip is None:
            return None
        self._deactivate_all_for_user(telegram_user_id)
        now = _now_iso()
        self._db.update(
            "trips",
            {"is_active": 1, "updated_at": now},
            "id = ?",
            (trip_id,),
        )
        return self.get_by_id(trip_id)

    def update_balances(
        self,
        trip_id: int,
        balance_home: float,
        balance_destination: float,
    ) -> None:
        self._db.update(
            "trips",
            {
                "balance_home": balance_home,
                "balance_destination": balance_destination,
                "updated_at": _now_iso(),
            },
            "id = ?",
            (trip_id,),
        )

    def update_rate(
        self,
        trip_id: int,
        rate: float,
        rate_source: str,
        balance_home: float,
        balance_destination: float,
    ) -> None:
        self._db.update(
            "trips",
            {
                "rate": rate,
                "rate_source": rate_source,
                "balance_home": balance_home,
                "balance_destination": balance_destination,
                "updated_at": _now_iso(),
            },
            "id = ?",
            (trip_id,),
        )

    def delete_trip(self, trip_id: int, telegram_user_id: int) -> bool:
        """Удаляет путешествие пользователя. Возвращает False, если не найдено."""
        if self.get_by_id_for_user(trip_id, telegram_user_id) is None:
            return False
        self._db.delete(
            "trips",
            "id = ? AND telegram_user_id = ?",
            (trip_id, telegram_user_id),
        )
        return True

    def _deactivate_all_for_user(self, telegram_user_id: int) -> None:
        self._db.update(
            "trips",
            {"is_active": 0, "updated_at": _now_iso()},
            "telegram_user_id = ?",
            (telegram_user_id,),
        )
