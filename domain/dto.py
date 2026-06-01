"""DTO — объекты для передачи результатов между слоями."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from domain.models import Expense, Trip


@dataclass
class ExpensePreview:
    """Предпросмотр расхода перед подтверждением."""

    amount_destination: float
    amount_home: float
    destination_currency: str
    home_currency: str
    rate: float
    would_be_negative: bool = False


@dataclass
class RateResult:
    """Результат получения курса валютной пары."""

    from_currency: str
    to_currency: str
    rate: float
    source: str  # api | manual | cache
    stale: bool = False
    warning: Optional[str] = None


@dataclass
class TripSummary:
    """Краткая информация о путешествии для списка."""

    trip: Trip
    is_active: bool


@dataclass
class BalanceView:
    """Отображение баланса активного путешествия."""

    trip: Trip
    rate_text: str
    balance_text: str


@dataclass
class CreateTripDraft:
    """Черновик данных при создании путешествия (хранится в user_states)."""

    home_country: Optional[str] = None
    home_currency: Optional[str] = None
    destination_country: Optional[str] = None
    destination_currency: Optional[str] = None
    rate: Optional[float] = None
    rate_source: Optional[str] = None
    awaiting_manual_home_currency: bool = False
    awaiting_manual_destination_currency: bool = False


@dataclass
class HistoryView:
    """История расходов для отображения."""

    trip_title: str
    expenses: List[Expense]
    empty: bool = False
