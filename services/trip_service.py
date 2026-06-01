"""
Бизнес-логика путешествий: создание, баланс, смена курса, переключение активного.
"""

from __future__ import annotations

from typing import List, Optional

from database_layer.expense_database import ExpenseDatabase
from database_layer.trip_database import TripDatabase
from database_layer.user_state_database import UserStateDatabase
from domain.dto import BalanceView, CreateTripDraft, RateResult, TripSummary
from domain.errors import NoActiveTripError, TripNotFoundError
from domain.models import Trip
from domain.number_utils import format_amount
from services.country_resolver_service import CountryResolverService
from services.currency_service import CurrencyService


class TripService:
    """Операции с путешествиями без привязки к Telegram."""

    def __init__(
        self,
        trip_db: TripDatabase,
        expense_db: ExpenseDatabase,
        currency_service: CurrencyService,
        user_state_db: UserStateDatabase,
        country_resolver: CountryResolverService,
    ) -> None:
        self._trips = trip_db
        self._expenses = expense_db
        self._currency = currency_service
        self._states = user_state_db
        self._countries = country_resolver

    @staticmethod
    def home_from_destination(amount_destination: float, rate: float) -> float:
        """Сумма в домашней валюте: amount_destination * rate."""
        return amount_destination * rate

    @staticmethod
    def destination_from_home(amount_home: float, rate: float) -> float:
        """Сумма в валюте пребывания: amount_home / rate."""
        return amount_home / rate

    def list_trips(self, telegram_user_id: int) -> List[TripSummary]:
        trips = self._trips.list_by_user(telegram_user_id)
        return [TripSummary(trip=t, is_active=t.is_active) for t in trips]

    def get_active_trip(self, telegram_user_id: int) -> Trip:
        trip = self._trips.get_active_trip(telegram_user_id)
        if trip is None:
            raise NoActiveTripError()
        return trip

    def get_active_trip_optional(self, telegram_user_id: int) -> Optional[Trip]:
        return self._trips.get_active_trip(telegram_user_id)

    def switch_active_trip(self, telegram_user_id: int, trip_id: int) -> Trip:
        trip = self._trips.set_active_trip(telegram_user_id, trip_id)
        if trip is None:
            raise TripNotFoundError()
        return trip

    def get_trip_for_user(self, telegram_user_id: int, trip_id: int) -> Trip:
        """Возвращает путешествие или TripNotFoundError."""
        trip = self._trips.get_by_id_for_user(trip_id, telegram_user_id)
        if trip is None:
            raise TripNotFoundError()
        return trip

    def delete_trip(self, telegram_user_id: int, trip_id: int) -> None:
        """Удаляет путешествие и все его расходы."""
        if self._trips.get_by_id_for_user(trip_id, telegram_user_id) is None:
            raise TripNotFoundError()
        self._expenses.delete_by_trip(trip_id)
        if not self._trips.delete_trip(trip_id, telegram_user_id):
            raise TripNotFoundError()

    def get_balance_view(self, telegram_user_id: int) -> BalanceView:
        trip = self.get_active_trip(telegram_user_id)
        return self._balance_view_from_trip(trip)

    def format_trip_balance_line(self, trip: Trip) -> str:
        """Строка баланса для списка путешествий."""
        dest = format_amount(trip.balance_destination)
        home = format_amount(trip.balance_home)
        return (
            f"Остаток: {dest} {trip.destination_currency} = "
            f"{home} {trip.home_currency}"
        )

    def format_rate_line(self, trip: Trip) -> str:
        return (
            f"1 {trip.destination_currency} = "
            f"{format_amount(trip.rate)} {trip.home_currency}"
        )

    def create_trip_from_draft(
        self,
        telegram_user_id: int,
        draft: CreateTripDraft,
        initial_balance_home: float,
    ) -> Trip:
        """Создаёт путешествие после заполнения черновика и начального баланса."""
        if not draft.home_currency or not draft.destination_currency or draft.rate is None:
            raise TripNotFoundError("Черновик путешествия не заполнен")

        balance_destination = self.destination_from_home(initial_balance_home, draft.rate)
        if draft.destination_country:
            title = draft.destination_country.strip().title()
        else:
            title = draft.destination_currency or "Путешествие"

        return self._trips.create_trip(
            telegram_user_id=telegram_user_id,
            title=title,
            home_country=draft.home_country,
            destination_country=draft.destination_country,
            home_currency=draft.home_currency,
            destination_currency=draft.destination_currency,
            rate=draft.rate,
            rate_source=draft.rate_source or "manual",
            balance_home=initial_balance_home,
            balance_destination=balance_destination,
            set_active=True,
        )

    def resolve_country_to_currency(self, country_text: str) -> Optional[str]:
        return self._countries.lookup_currency_by_country(country_text)

    def fetch_trip_rate(
        self,
        destination_currency: str,
        home_currency: str,
        *,
        force_refresh: bool = False,
    ) -> RateResult:
        """
        Курс для путешествия: 1 destination = X home.

        API: from=destination, to=home, amount=1.
        """
        return self._currency.get_exchange_rate(
            destination_currency,
            home_currency,
            force_refresh=force_refresh,
        )

    def update_trip_rate(
        self,
        telegram_user_id: int,
        new_rate: float,
        rate_source: str,
    ) -> Trip:
        """
        Обновляет курс; баланс в валюте пребывания не меняется,
        домашний пересчитывается: balance_home = balance_destination * rate.
        """
        trip = self.get_active_trip(telegram_user_id)
        new_balance_home = self.home_from_destination(trip.balance_destination, new_rate)
        self._trips.update_rate(
            trip.id,
            new_rate,
            rate_source,
            new_balance_home,
            trip.balance_destination,
        )
        updated = self._trips.get_by_id(trip.id)
        assert updated is not None
        return updated

    def refresh_active_trip_rate_from_api(self, telegram_user_id: int) -> tuple[Trip, Optional[str]]:
        """Обновляет курс активного путешествия через API/кэш."""
        trip = self.get_active_trip(telegram_user_id)
        rate_result = self.fetch_trip_rate(
            trip.destination_currency,
            trip.home_currency,
            force_refresh=False,
        )
        updated = self.update_trip_rate(
            telegram_user_id,
            rate_result.rate,
            rate_result.source,
        )
        return updated, rate_result.warning

    def _balance_view_from_trip(self, trip: Trip) -> BalanceView:
        dest = format_amount(trip.balance_destination)
        home = format_amount(trip.balance_home)
        return BalanceView(
            trip=trip,
            rate_text=self.format_rate_line(trip),
            balance_text=(
                f"{dest} {trip.destination_currency} = {home} {trip.home_currency}"
            ),
        )
