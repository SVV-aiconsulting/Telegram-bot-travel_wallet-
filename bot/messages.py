"""Тексты сообщений бота."""

from __future__ import annotations

from domain.dto import ExpensePreview
from domain.models import Trip
from domain.number_utils import format_amount
from services.expense_service import ExpenseService
from services.trip_service import TripService


def expense_input_hint(trip: Trip) -> str:
    """Подсказка: как быстро записать расход числом в чат."""
    return (
        f"\n\n💡 *Для учёта расхода* отправьте сумму в *{trip.destination_currency}*, "
        f"например: `100` или `99.50`.\n"
        f"Я пересчитаю в {trip.home_currency} и попрошу подтвердить."
    )


def main_menu_text(trip: Trip | None = None) -> str:
    base = (
        "🏠 *Миникошелёк путешественника*\n\n"
        "Учитывайте расходы в поездке с конвертацией в домашнюю валюту.\n"
        "Выберите действие в меню ниже."
    )
    if trip is not None:
        return base + expense_input_hint(trip)
    return (
        base
        + "\n\n💡 Сначала создайте или выберите путешествие — "
        "после этого можно вводить суммы расходов числом."
    )


def trip_detail_text(trip: Trip, trip_service: TripService) -> str:
    """Карточка путешествия перед выбором действия."""
    active_mark = "✅ Активное\n\n" if trip.is_active else ""
    return (
        f"{active_mark}*{trip.title}*\n"
        f"{trip.destination_currency}/{trip.home_currency}\n"
        f"Курс: {trip_service.format_rate_line(trip)}\n"
        f"{trip_service.format_trip_balance_line(trip)}"
    )


def no_active_trip_text() -> str:
    return (
        "У вас пока нет активного путешествия.\n"
        "Создайте новое путешествие или выберите одно из существующих."
    )


def trip_created_summary(trip: Trip, trip_service: TripService) -> str:
    dest = format_amount(trip.balance_destination)
    home = format_amount(trip.balance_home)
    return (
        f"✅ Путешествие создано!\n\n"
        f"*{trip.title}*\n"
        f"{trip.destination_currency}/{trip.home_currency}\n"
        f"Курс: {trip_service.format_rate_line(trip)}\n"
        f"Баланс: {dest} {trip.destination_currency} = {home} {trip.home_currency}"
        + expense_input_hint(trip)
    )


def balance_text(
    title: str,
    rate_line: str,
    balance_line: str,
    trip: Trip | None = None,
) -> str:
    text = (
        f"Активное путешествие: *{title}*\n\n"
        f"Курс:\n{rate_line}\n\n"
        f"Остаток:\n{balance_line}"
    )
    if trip is not None:
        text += expense_input_hint(trip)
    return text


def expense_confirm_text(preview: ExpensePreview, expense_service: ExpenseService) -> str:
    line = expense_service.format_preview_line(preview)
    text = f"{line}\n\nУчесть как расход?"
    if preview.would_be_negative:
        text += (
            "\n\n⚠️ *Внимание:* после этого расхода баланс станет отрицательным."
        )
    return text


def expense_recorded_text(trip: Trip) -> str:
    dest = format_amount(trip.balance_destination)
    home = format_amount(trip.balance_home)
    return (
        f"Расход учтён ✅\n\n"
        f"Остаток:\n{dest} {trip.destination_currency} = {home} {trip.home_currency}"
        + expense_input_hint(trip)
    )
