"""Inline-клавиатуры Telegram-бота."""

from __future__ import annotations

from telebot import types

from domain.models import Trip


def main_menu_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("➕ Создать новое путешествие", callback_data="trip_create"),
        types.InlineKeyboardButton("🧳 Мои путешествия", callback_data="trip_list"),
        types.InlineKeyboardButton("💰 Баланс", callback_data="balance"),
        types.InlineKeyboardButton("📜 История расходов", callback_data="history"),
        types.InlineKeyboardButton("💱 Изменить курс", callback_data="rate_change"),
    )
    return kb


def back_to_menu_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="menu"))
    return kb


def rate_confirm_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✅ Да", callback_data="rate_confirm_yes"),
        types.InlineKeyboardButton("✏️ Ввести вручную", callback_data="rate_manual"),
        types.InlineKeyboardButton("❌ Отмена", callback_data="trip_cancel"),
    )
    return kb


def expense_confirm_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✅ Да", callback_data="expense_confirm"),
        types.InlineKeyboardButton("❌ Нет", callback_data="expense_cancel"),
    )
    return kb


def rate_change_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("✏️ Ввести вручную", callback_data="rate_change_manual"),
        types.InlineKeyboardButton("🔄 Обновить через API", callback_data="rate_api"),
        types.InlineKeyboardButton("❌ Отмена", callback_data="menu"),
    )
    return kb


def trip_list_keyboard(trips: list[Trip]) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    for trip in trips:
        prefix = "✅ " if trip.is_active else ""
        kb.add(
            types.InlineKeyboardButton(
                f"{prefix}{trip.title}",
                callback_data=f"trip_select:{trip.id}",
            )
        )
    kb.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="menu"))
    return kb


def trip_actions_keyboard(trip_id: int, is_active: bool) -> types.InlineKeyboardMarkup:
    """Действия с выбранным путешествием: активировать / удалить."""
    kb = types.InlineKeyboardMarkup(row_width=1)
    if not is_active:
        kb.add(
            types.InlineKeyboardButton(
                "✅ Сделать активным",
                callback_data=f"trip_activate:{trip_id}",
            )
        )
    kb.add(
        types.InlineKeyboardButton(
            "🗑 Удалить путешествие",
            callback_data=f"trip_delete:{trip_id}",
        )
    )
    kb.add(
        types.InlineKeyboardButton("◀️ К списку", callback_data="trip_list"),
        types.InlineKeyboardButton("🏠 Главное меню", callback_data="menu"),
    )
    return kb


def trip_delete_confirm_keyboard(trip_id: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton(
            "✅ Да, удалить",
            callback_data=f"trip_delete_confirm:{trip_id}",
        ),
        types.InlineKeyboardButton(
            "❌ Отмена",
            callback_data=f"trip_select:{trip_id}",
        ),
    )
    return kb


def rate_api_failed_keyboard() -> types.InlineKeyboardMarkup:
    """Если курс с API не получен при создании путешествия."""
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton(
            "🔄 Повторить запрос к API",
            callback_data="rate_retry_api",
        ),
        types.InlineKeyboardButton(
            "✏️ Ввести курс вручную",
            callback_data="rate_manual",
        ),
        types.InlineKeyboardButton("❌ Отмена", callback_data="trip_cancel"),
    )
    return kb
