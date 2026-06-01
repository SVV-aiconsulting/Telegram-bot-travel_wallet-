"""
Сервис сценария создания путешествия (черновик + шаги FSM).
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Optional, Tuple

from database_layer.user_state_database import UserStateDatabase
from services.country_resolver_service import CountryResolverService
from domain.dto import CreateTripDraft, RateResult
from domain.errors import CurrencyApiError, CurrencyNotFoundError
from domain.number_utils import parse_positive_amount
from services.currency_service import CurrencyService
from services.trip_service import TripService

DRAFT_KEY = "trip_draft"


class CreationService:
    """Управление черновиком и шагами создания путешествия."""

    def __init__(
        self,
        user_state_db: UserStateDatabase,
        trip_service: TripService,
        currency_service: CurrencyService,
        country_resolver: CountryResolverService,
    ) -> None:
        self._states = user_state_db
        self._trips = trip_service
        self._currency = currency_service
        self._countries = country_resolver

    def start_creation(self, telegram_user_id: int) -> None:
        from domain.states import BotState

        self._states.set_state(telegram_user_id, BotState.TRIP_HOME_COUNTRY.value, {DRAFT_KEY: {}})

    def cancel_creation(self, telegram_user_id: int) -> None:
        self._states.clear_state(telegram_user_id)

    def get_draft(self, telegram_user_id: int) -> CreateTripDraft:
        payload = self._states.get_payload(telegram_user_id)
        raw = payload.get(DRAFT_KEY, {})
        return CreateTripDraft(
            home_country=raw.get("home_country"),
            home_currency=raw.get("home_currency"),
            destination_country=raw.get("destination_country"),
            destination_currency=raw.get("destination_currency"),
            rate=raw.get("rate"),
            rate_source=raw.get("rate_source"),
            awaiting_manual_home_currency=raw.get("awaiting_manual_home_currency", False),
            awaiting_manual_destination_currency=raw.get(
                "awaiting_manual_destination_currency", False
            ),
        )

    def _save_draft(self, telegram_user_id: int, draft: CreateTripDraft, state: str) -> None:
        payload = {DRAFT_KEY: {k: v for k, v in asdict(draft).items() if v is not None}}
        self._states.set_state(telegram_user_id, state, payload)

    def set_home_country(self, telegram_user_id: int, text: str) -> Tuple[CreateTripDraft, bool]:
        """
        Обрабатывает страну отправления.

        Returns:
            (draft, needs_manual_currency)
        """
        from domain.states import BotState

        draft = self.get_draft(telegram_user_id)
        draft.home_country = text.strip()
        currency = self._countries.lookup_currency_by_country(text)
        if currency:
            draft.home_currency = currency
            draft.awaiting_manual_home_currency = False
            self._save_draft(telegram_user_id, draft, BotState.TRIP_DESTINATION_COUNTRY.value)
            return draft, False

        draft.awaiting_manual_home_currency = True
        self._save_draft(telegram_user_id, draft, BotState.TRIP_HOME_CURRENCY.value)
        return draft, True

    def set_home_currency_manual(self, telegram_user_id: int, code: str) -> CreateTripDraft:
        from domain.states import BotState

        currency = self._countries.resolve_currency_input(code)
        if not currency:
            raise CurrencyNotFoundError()
        draft = self.get_draft(telegram_user_id)
        draft.home_currency = currency
        draft.awaiting_manual_home_currency = False
        self._save_draft(telegram_user_id, draft, BotState.TRIP_DESTINATION_COUNTRY.value)
        return draft

    def set_destination_country(self, telegram_user_id: int, text: str) -> Tuple[CreateTripDraft, bool]:
        from domain.states import BotState

        draft = self.get_draft(telegram_user_id)
        draft.destination_country = text.strip()
        currency = self._countries.lookup_currency_by_country(text)
        if currency:
            draft.destination_currency = currency
            draft.awaiting_manual_destination_currency = False
            self._save_draft(telegram_user_id, draft, BotState.TRIP_RATE_CONFIRM.value)
            return draft, False

        draft.awaiting_manual_destination_currency = True
        self._save_draft(telegram_user_id, draft, BotState.TRIP_DESTINATION_CURRENCY.value)
        return draft, True

    def set_destination_currency_manual(self, telegram_user_id: int, code: str) -> CreateTripDraft:
        from domain.states import BotState

        currency = self._countries.resolve_currency_input(code)
        if not currency:
            raise CurrencyNotFoundError()
        draft = self.get_draft(telegram_user_id)
        draft.destination_currency = currency
        draft.awaiting_manual_destination_currency = False
        self._save_draft(telegram_user_id, draft, BotState.TRIP_RATE_CONFIRM.value)
        return draft

    def fetch_rate_for_draft(
        self,
        telegram_user_id: int,
        *,
        force_refresh: bool = False,
    ) -> RateResult:
        draft = self.get_draft(telegram_user_id)
        if not draft.destination_currency or not draft.home_currency:
            raise CurrencyNotFoundError("Валюты не заданы")
        return self._trips.fetch_trip_rate(
            draft.destination_currency,
            draft.home_currency,
            force_refresh=force_refresh,
        )

    def set_draft_rate(
        self,
        telegram_user_id: int,
        rate: float,
        rate_source: str,
    ) -> CreateTripDraft:
        """Сохраняет курс в черновик, ожидая подтверждения пользователя."""
        from domain.states import BotState

        draft = self.get_draft(telegram_user_id)
        draft.rate = rate
        draft.rate_source = rate_source
        self._save_draft(telegram_user_id, draft, BotState.TRIP_RATE_CONFIRM.value)
        return draft

    def confirm_rate_and_ask_balance(self, telegram_user_id: int) -> CreateTripDraft:
        """После «Да» переводит на шаг ввода начального баланса."""
        from domain.states import BotState

        draft = self.get_draft(telegram_user_id)
        if draft.rate is None:
            raise CurrencyNotFoundError("Сначала укажите курс")
        self._save_draft(telegram_user_id, draft, BotState.TRIP_INITIAL_BALANCE.value)
        return draft

    def set_manual_rate(self, telegram_user_id: int, rate_text: str) -> CreateTripDraft:
        from domain.states import BotState

        rate = parse_positive_amount(rate_text)
        draft = self.get_draft(telegram_user_id)
        if not draft.destination_currency or not draft.home_currency:
            raise CurrencyNotFoundError()
        self._currency.set_manual_rate(
            draft.destination_currency,
            draft.home_currency,
            rate,
        )
        draft.rate = rate
        draft.rate_source = "manual"
        self._save_draft(telegram_user_id, draft, BotState.TRIP_INITIAL_BALANCE.value)
        return draft

    def complete_with_balance(self, telegram_user_id: int, balance_text: str):
        from domain.models import Trip

        draft = self.get_draft(telegram_user_id)
        balance_home = parse_positive_amount(balance_text)
        trip = self._trips.create_trip_from_draft(telegram_user_id, draft, balance_home)
        self._states.clear_state(telegram_user_id)
        return trip

    def move_to_manual_rate(self, telegram_user_id: int) -> None:
        from domain.states import BotState

        draft = self.get_draft(telegram_user_id)
        self._save_draft(telegram_user_id, draft, BotState.TRIP_RATE_MANUAL.value)

    def stay_on_rate_confirm(self, telegram_user_id: int) -> CreateTripDraft:
        """Оставляет шаг подтверждения курса (после ошибки API)."""
        from domain.states import BotState

        draft = self.get_draft(telegram_user_id)
        self._save_draft(telegram_user_id, draft, BotState.TRIP_RATE_CONFIRM.value)
        return draft
