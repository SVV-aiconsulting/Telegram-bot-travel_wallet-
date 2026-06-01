"""Состояния диалога (FSM), общие для backend и Telegram."""

from __future__ import annotations

from enum import Enum


class BotState(str, Enum):
    """Имена состояний в таблице user_states."""

    TRIP_HOME_COUNTRY = "trip_home_country"
    TRIP_HOME_CURRENCY = "trip_home_currency"
    TRIP_DESTINATION_COUNTRY = "trip_destination_country"
    TRIP_DESTINATION_CURRENCY = "trip_destination_currency"
    TRIP_RATE_CONFIRM = "trip_rate_confirm"
    TRIP_RATE_MANUAL = "trip_rate_manual"
    TRIP_INITIAL_BALANCE = "trip_initial_balance"
    RATE_CHANGE_MANUAL = "rate_change_manual"
