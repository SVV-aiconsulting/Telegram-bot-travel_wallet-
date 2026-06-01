"""Слой доступа к данным расходов."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from database import SQLiteDatabaseManager
from domain.models import Expense


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _row_to_expense(row) -> Expense:
    return Expense(
        id=row["id"],
        trip_id=row["trip_id"],
        telegram_user_id=row["telegram_user_id"],
        amount_destination=float(row["amount_destination"]),
        amount_home=float(row["amount_home"]),
        rate=float(row["rate"]),
        created_at=row["created_at"],
        comment=row["comment"],
    )


class ExpenseDatabase:
    """CRUD для таблицы expenses."""

    def __init__(self, db: SQLiteDatabaseManager) -> None:
        self._db = db

    def add_expense(
        self,
        trip_id: int,
        telegram_user_id: int,
        amount_destination: float,
        amount_home: float,
        rate: float,
        comment: Optional[str] = None,
    ) -> Expense:
        expense_id = self._db.insert(
            "expenses",
            {
                "trip_id": trip_id,
                "telegram_user_id": telegram_user_id,
                "amount_destination": amount_destination,
                "amount_home": amount_home,
                "rate": rate,
                "created_at": _now_iso(),
                "comment": comment,
            },
        )
        expense = self.get_by_id(expense_id)
        assert expense is not None
        return expense

    def get_by_id(self, expense_id: int) -> Optional[Expense]:
        row = self._db.select_one("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        return _row_to_expense(row) if row else None

    def delete_by_trip(self, trip_id: int) -> int:
        """Удаляет все расходы путешествия (перед удалением поездки)."""
        return self._db.delete("expenses", "trip_id = ?", (trip_id,))

    def list_recent_for_trip(self, trip_id: int, limit: int = 10) -> List[Expense]:
        rows = self._db.select_all(
            """
            SELECT * FROM expenses
            WHERE trip_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (trip_id, limit),
        )
        return [_row_to_expense(r) for r in rows]
