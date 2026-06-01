"""Сервис изменения курса активного путешествия."""

from __future__ import annotations

from database_layer.user_state_database import UserStateDatabase
from domain.errors import CurrencyNotFoundError
from domain.number_utils import parse_positive_amount
from domain.models import Trip
from services.trip_service import TripService


class RateChangeService:
    """Сценарий смены курса (ручной ввод / API)."""

    def __init__(
        self,
        trip_service: TripService,
        user_state_db: UserStateDatabase,
    ) -> None:
        self._trips = trip_service
        self._states = user_state_db

    def start_manual_rate_change(self, telegram_user_id: int) -> None:
        from domain.states import BotState

        self._states.set_state(telegram_user_id, BotState.RATE_CHANGE_MANUAL.value, {})

    def cancel_rate_change(self, telegram_user_id: int) -> None:
        self._states.clear_state(telegram_user_id)

    def apply_manual_rate(self, telegram_user_id: int, rate_text: str) -> Trip:
        rate = parse_positive_amount(rate_text)
        trip = self._trips.update_trip_rate(telegram_user_id, rate, "manual")
        self._states.clear_state(telegram_user_id)
        return trip

    def refresh_from_api(self, telegram_user_id: int) -> tuple[Trip, str | None]:
        trip, warning = self._trips.refresh_active_trip_rate_from_api(telegram_user_id)
        return trip, warning
