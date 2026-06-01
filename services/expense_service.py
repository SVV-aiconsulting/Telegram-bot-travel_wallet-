"""
Бизнес-логика расходов: предпросмотр, подтверждение, история.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from database_layer.expense_database import ExpenseDatabase
from database_layer.trip_database import TripDatabase
from database_layer.user_state_database import UserStateDatabase
from domain.dto import ExpensePreview, HistoryView
from domain.errors import NoActiveTripError
from domain.models import Expense, Trip
from domain.number_utils import format_amount
from services.trip_service import TripService

PENDING_EXPENSE_KEY = "pending_expense"


class ExpenseService:
    """Учёт расходов в активном путешествии."""

    def __init__(
        self,
        expense_db: ExpenseDatabase,
        trip_db: TripDatabase,
        trip_service: TripService,
        user_state_db: UserStateDatabase,
    ) -> None:
        self._expenses = expense_db
        self._trips = trip_db
        self._trip_service = trip_service
        self._states = user_state_db

    def preview_expense(self, telegram_user_id: int, amount_destination: float) -> ExpensePreview:
        """Считает расход и проверяет, уйдёт ли баланс в минус."""
        trip = self._trip_service.get_active_trip(telegram_user_id)
        amount_home = TripService.home_from_destination(amount_destination, trip.rate)
        new_dest_balance = trip.balance_destination - amount_destination
        would_be_negative = new_dest_balance < 0
        return ExpensePreview(
            amount_destination=amount_destination,
            amount_home=amount_home,
            destination_currency=trip.destination_currency,
            home_currency=trip.home_currency,
            rate=trip.rate,
            would_be_negative=would_be_negative,
        )

    def save_pending_expense(self, telegram_user_id: int, preview: ExpensePreview) -> None:
        """Сохраняет предпросмотр расхода в user_states для подтверждения."""
        payload = self._states.get_payload(telegram_user_id)
        payload[PENDING_EXPENSE_KEY] = {
            "amount_destination": preview.amount_destination,
            "amount_home": preview.amount_home,
            "rate": preview.rate,
        }
        current = self._states.get_state(telegram_user_id)
        self._states.set_state(
            telegram_user_id,
            current.state if current else None,
            payload,
        )

    def get_pending_expense(self, telegram_user_id: int) -> Optional[dict]:
        return self._states.get_payload(telegram_user_id).get(PENDING_EXPENSE_KEY)

    def clear_pending_expense(self, telegram_user_id: int) -> None:
        payload = self._states.get_payload(telegram_user_id)
        payload.pop(PENDING_EXPENSE_KEY, None)
        current = self._states.get_state(telegram_user_id)
        self._states.set_state(
            telegram_user_id,
            current.state if current else None,
            payload,
        )

    def confirm_expense(self, telegram_user_id: int) -> Trip:
        """Записывает расход и уменьшает баланс."""
        pending = self.get_pending_expense(telegram_user_id)
        if not pending:
            raise NoActiveTripError("Нет ожидающего расхода")

        trip = self._trip_service.get_active_trip(telegram_user_id)
        amount_dest = float(pending["amount_destination"])
        amount_home = float(pending["amount_home"])
        rate = float(pending["rate"])

        self._expenses.add_expense(
            trip_id=trip.id,
            telegram_user_id=telegram_user_id,
            amount_destination=amount_dest,
            amount_home=amount_home,
            rate=rate,
        )

        new_dest = trip.balance_destination - amount_dest
        new_home = trip.balance_home - amount_home
        self._trips.update_balances(trip.id, new_home, new_dest)
        self.clear_pending_expense(telegram_user_id)

        updated = self._trips.get_by_id(trip.id)
        assert updated is not None
        return updated

    def get_history(self, telegram_user_id: int, limit: int = 10) -> HistoryView:
        trip = self._trip_service.get_active_trip(telegram_user_id)
        expenses = self._expenses.list_recent_for_trip(trip.id, limit=limit)
        return HistoryView(
            trip_title=trip.title,
            expenses=expenses,
            empty=len(expenses) == 0,
        )

    @staticmethod
    def format_expense_line(expense: Expense, trip: Trip) -> str:
        """Одна строка истории с датой."""
        try:
            dt = datetime.strptime(expense.created_at, "%Y-%m-%d %H:%M:%S")
            date_str = dt.strftime("%d.%m.%Y %H:%M")
        except ValueError:
            date_str = expense.created_at

        dest = format_amount(expense.amount_destination)
        home = format_amount(expense.amount_home)
        return (
            f"{date_str}\n"
            f"{dest} {trip.destination_currency} = {home} {trip.home_currency}"
        )

    @staticmethod
    def format_preview_line(preview: ExpensePreview) -> str:
        dest = format_amount(preview.amount_destination)
        home = format_amount(preview.amount_home)
        return f"{dest} {preview.destination_currency} = {home} {preview.home_currency}"
