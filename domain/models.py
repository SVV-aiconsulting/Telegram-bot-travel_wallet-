"""Модели данных доменного слоя."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Trip:
    """Путешествие пользователя с балансом и курсом."""

    id: int
    telegram_user_id: int
    title: str
    home_country: Optional[str]
    destination_country: Optional[str]
    home_currency: str
    destination_currency: str
    rate: float
    rate_source: str
    balance_home: float
    balance_destination: float
    is_active: bool
    created_at: str
    updated_at: str


@dataclass
class Expense:
    """Запись о расходе в рамках путешествия."""

    id: int
    trip_id: int
    telegram_user_id: int
    amount_destination: float
    amount_home: float
    rate: float
    created_at: str
    comment: Optional[str] = None


@dataclass
class RateCacheEntry:
    """Кэшированный курс валютной пары."""

    id: int
    from_currency: str
    to_currency: str
    rate: float
    updated_at: str


@dataclass
class UserState:
    """Состояние диалога пользователя (FSM)."""

    telegram_user_id: int
    state: Optional[str]
    payload_json: Optional[str]
    updated_at: str
