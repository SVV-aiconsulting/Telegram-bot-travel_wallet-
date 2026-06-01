"""
Обработчики Telegram: сообщения, команды и callback.

Бизнес-логика делегируется сервисам из container; SQL и API здесь не вызываются.
"""

from __future__ import annotations

import logging

import telebot
from telebot import types

from bot import keyboards, messages
from bot.states import BotState
from container import AppContainer
from domain.errors import (
    AppError,
    CurrencyApiError,
    CurrencyNotFoundError,
    InvalidAmountError,
    NoActiveTripError,
    TripNotFoundError,
)
from domain.number_utils import format_amount, parse_positive_amount
from services.expense_service import ExpenseService
from services.trip_service import TripService

logger = logging.getLogger(__name__)

# Текст без слэша — то же, что команды /start и /menu
_MENU_TEXT_ALIASES = frozenset(
    {"старт", "start", "меню", "menu", "главное меню", "главное", "help", "помощь"}
)


def register_handlers(bot: telebot.TeleBot, container: AppContainer) -> None:
    """Регистрирует все обработчики на экземпляре бота."""

    trip_svc = container.trip_service
    expense_svc = container.expense_service
    creation_svc = container.creation_service
    rate_change_svc = container.rate_change_service
    state_db = container.user_state_db

    def user_id(message: types.Message) -> int:
        return message.from_user.id

    def cb_user_id(call: types.CallbackQuery) -> int:
        return call.from_user.id

    def send_menu(chat_id: int, uid: int | None = None, text: str | None = None) -> None:
        if text is None:
            active = trip_svc.get_active_trip_optional(uid) if uid is not None else None
            text = messages.main_menu_text(active)
        bot.send_message(
            chat_id,
            text,
            reply_markup=keyboards.main_menu_keyboard(),
            parse_mode="Markdown",
        )

    def friendly_error(chat_id: int, exc: Exception) -> None:
        mapping = {
            InvalidAmountError: (
                "Я не смог распознать сумму.\n"
                "Введите число, например: 100 или 99.50"
            ),
            CurrencyNotFoundError: (
                "Не нашёл валюту для этой страны.\n"
                "Введите код валюты (RUB, USD, CNY) или повторите название страны."
            ),
            CurrencyApiError: (
                "Сейчас не получилось получить курс через API.\n"
                "Можно ввести курс вручную."
            ),
            NoActiveTripError: messages.no_active_trip_text(),
            TripNotFoundError: "Путешествие не найдено.",
        }
        text = mapping.get(type(exc), "Произошла ошибка. Попробуйте ещё раз или вернитесь в меню.")
        if isinstance(exc, AppError) and exc.message and type(exc) not in mapping:
            text = exc.message
        bot.send_message(chat_id, text, reply_markup=keyboards.back_to_menu_keyboard())

    def is_in_dialog(user: int) -> bool:
        st = state_db.get_state(user)
        return st is not None and st.state is not None

    # --- Команды ---

    @bot.message_handler(commands=["start", "menu"])
    def cmd_start(message: types.Message) -> None:
        send_menu(message.chat.id, user_id(message))

    @bot.message_handler(commands=["newtrip"])
    def cmd_newtrip(message: types.Message) -> None:
        start_trip_creation(message.chat.id, user_id(message))

    @bot.message_handler(commands=["switch"])
    def cmd_switch(message: types.Message) -> None:
        show_trip_list(message.chat.id, user_id(message))

    @bot.message_handler(commands=["balance"])
    def cmd_balance(message: types.Message) -> None:
        show_balance(message.chat.id, user_id(message))

    @bot.message_handler(commands=["history"])
    def cmd_history(message: types.Message) -> None:
        show_history(message.chat.id, user_id(message))

    @bot.message_handler(commands=["setrate"])
    def cmd_setrate(message: types.Message) -> None:
        show_rate_change(message.chat.id, user_id(message))

    def start_trip_creation(chat_id: int, uid: int) -> None:
        creation_svc.start_creation(uid)
        bot.send_message(
            chat_id,
            "Создание нового путешествия.\n\nВведите *страну отправления* (домашнюю):",
            parse_mode="Markdown",
        )

    def show_balance(chat_id: int, uid: int) -> None:
        try:
            view = trip_svc.get_balance_view(uid)
            bot.send_message(
                chat_id,
                messages.balance_text(
                    view.trip.title,
                    view.rate_text,
                    view.balance_text,
                    trip=view.trip,
                ),
                reply_markup=keyboards.back_to_menu_keyboard(),
                parse_mode="Markdown",
            )
        except NoActiveTripError as exc:
            friendly_error(chat_id, exc)

    def show_history(chat_id: int, uid: int) -> None:
        try:
            history = expense_svc.get_history(uid)
            trip = trip_svc.get_active_trip(uid)
            if history.empty:
                bot.send_message(
                    chat_id,
                    "Пока расходов нет." + messages.expense_input_hint(trip),
                    reply_markup=keyboards.back_to_menu_keyboard(),
                    parse_mode="Markdown",
                )
                return
            lines = [f"История расходов: *{history.trip_title}*\n"]
            for exp in history.expenses:
                lines.append(expense_svc.format_expense_line(exp, trip))
                lines.append("")
            bot.send_message(
                chat_id,
                "\n".join(lines).strip(),
                reply_markup=keyboards.back_to_menu_keyboard(),
                parse_mode="Markdown",
            )
        except NoActiveTripError as exc:
            friendly_error(chat_id, exc)

    def show_trip_list(chat_id: int, uid: int) -> None:
        summaries = trip_svc.list_trips(uid)
        if not summaries:
            bot.send_message(
                chat_id,
                "У вас пока нет путешествий.\nСоздайте первое через меню.",
                reply_markup=keyboards.main_menu_keyboard(),
            )
            return
        lines = ["*Ваши путешествия:*\n"]
        for s in summaries:
            prefix = "✅ " if s.is_active else ""
            t = s.trip
            lines.append(f"{prefix}*{t.title}*")
            lines.append(f"{t.destination_currency}/{t.home_currency}")
            lines.append(trip_svc.format_trip_balance_line(t))
            lines.append("")
        bot.send_message(
            chat_id,
            "\n".join(lines).strip(),
            reply_markup=keyboards.trip_list_keyboard([s.trip for s in summaries]),
            parse_mode="Markdown",
        )

    def show_rate_change(chat_id: int, uid: int) -> None:
        try:
            trip = trip_svc.get_active_trip(uid)
            bot.send_message(
                chat_id,
                f"Текущий курс:\n{trip_svc.format_rate_line(trip)}\n\nЧто сделать?",
                reply_markup=keyboards.rate_change_keyboard(),
            )
        except NoActiveTripError as exc:
            friendly_error(chat_id, exc)

    # --- Callback ---

    @bot.callback_query_handler(func=lambda c: True)
    def on_callback(call: types.CallbackQuery) -> None:
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        data = call.data or ""
        chat_id = call.message.chat.id
        uid = cb_user_id(call)

        try:
            if data == "menu":
                send_menu(chat_id, uid)
            elif data == "trip_create":
                start_trip_creation(chat_id, uid)
            elif data == "trip_list":
                show_trip_list(chat_id, uid)
            elif data == "balance":
                show_balance(chat_id, uid)
            elif data == "history":
                show_history(chat_id, uid)
            elif data == "rate_change":
                show_rate_change(chat_id, uid)
            elif data == "trip_cancel":
                creation_svc.cancel_creation(uid)
                rate_change_svc.cancel_rate_change(uid)
                bot.send_message(chat_id, "Создание отменено.", reply_markup=keyboards.main_menu_keyboard())
            elif data == "rate_confirm_yes":
                _handle_rate_confirm_yes(chat_id, uid)
            elif data == "rate_retry_api":
                draft = creation_svc.get_draft(uid)
                _show_rate_and_confirm(chat_id, uid, draft, force_refresh=True)
            elif data == "rate_manual":
                creation_svc.move_to_manual_rate(uid)
                draft = creation_svc.get_draft(uid)
                bot.send_message(
                    chat_id,
                    f"Введите курс: сколько {draft.home_currency} стоит 1 {draft.destination_currency}",
                )
            elif data == "expense_confirm":
                _handle_expense_confirm(chat_id, uid)
            elif data == "expense_cancel":
                expense_svc.clear_pending_expense(uid)
                bot.send_message(chat_id, "Ок, расход не записан.", reply_markup=keyboards.main_menu_keyboard())
            elif data == "rate_change_manual":
                rate_change_svc.start_manual_rate_change(uid)
                trip = trip_svc.get_active_trip(uid)
                bot.send_message(
                    chat_id,
                    f"Введите новый курс: сколько {trip.home_currency} стоит 1 {trip.destination_currency}",
                )
            elif data == "rate_api":
                _handle_rate_api_refresh(chat_id, uid)
            elif data.startswith("trip_select:"):
                trip_id = int(data.split(":", 1)[1])
                _show_trip_actions(chat_id, uid, trip_id)
            elif data.startswith("trip_activate:"):
                trip_id = int(data.split(":", 1)[1])
                trip = trip_svc.switch_active_trip(uid, trip_id)
                bot.send_message(
                    chat_id,
                    f"Активное путешествие: *{trip.title}*"
                    + messages.expense_input_hint(trip),
                    reply_markup=keyboards.back_to_menu_keyboard(),
                    parse_mode="Markdown",
                )
            elif data.startswith("trip_delete:"):
                trip_id = int(data.split(":", 1)[1])
                trip = trip_svc.get_trip_for_user(uid, trip_id)
                bot.send_message(
                    chat_id,
                    f"Удалить путешествие *{trip.title}*?\n"
                    "Все расходы по нему тоже будут удалены.",
                    reply_markup=keyboards.trip_delete_confirm_keyboard(trip_id),
                    parse_mode="Markdown",
                )
            elif data.startswith("trip_delete_confirm:"):
                trip_id = int(data.split(":", 1)[1])
                trip_svc.delete_trip(uid, trip_id)
                bot.send_message(
                    chat_id,
                    "Путешествие удалено.",
                    reply_markup=keyboards.main_menu_keyboard(),
                )
            else:
                bot.send_message(
                    chat_id,
                    "Эта кнопка устарела. Откройте главное меню.",
                    reply_markup=keyboards.main_menu_keyboard(),
                )
        except (ValueError, IndexError):
            bot.send_message(
                chat_id,
                "Эта кнопка устарела. Откройте главное меню.",
                reply_markup=keyboards.main_menu_keyboard(),
            )
        except AppError as exc:
            friendly_error(chat_id, exc)

    def _handle_rate_confirm_yes(chat_id: int, uid: int) -> None:
        draft = creation_svc.get_draft(uid)
        if draft.rate is None:
            rate_result = creation_svc.fetch_rate_for_draft(uid)
            creation_svc.set_draft_rate(uid, rate_result.rate, rate_result.source)
            draft = creation_svc.get_draft(uid)
        draft = creation_svc.confirm_rate_and_ask_balance(uid)
        bot.send_message(
            chat_id,
            f"Введите начальную сумму в {draft.home_currency}:",
        )

    def _handle_rate_api_refresh(chat_id: int, uid: int) -> None:
        trip, warning = rate_change_svc.refresh_from_api(uid)
        text = f"Курс обновлён:\n{trip_svc.format_rate_line(trip)}\n\n"
        dest = format_amount(trip.balance_destination)
        home = format_amount(trip.balance_home)
        text += f"Остаток:\n{dest} {trip.destination_currency} = {home} {trip.home_currency}"
        if warning:
            text = f"⚠️ {warning}\n\n" + text
        bot.send_message(chat_id, text, reply_markup=keyboards.back_to_menu_keyboard())

    def _handle_expense_confirm(chat_id: int, uid: int) -> None:
        trip = expense_svc.confirm_expense(uid)
        bot.send_message(
            chat_id,
            messages.expense_recorded_text(trip),
            reply_markup=keyboards.back_to_menu_keyboard(),
        )

    def _show_trip_actions(chat_id: int, uid: int, trip_id: int) -> None:
        trip = trip_svc.get_trip_for_user(uid, trip_id)
        bot.send_message(
            chat_id,
            messages.trip_detail_text(trip, trip_svc) + "\n\nЧто сделать?",
            reply_markup=keyboards.trip_actions_keyboard(trip.id, trip.is_active),
            parse_mode="Markdown",
        )

    # --- Текстовые сообщения (FSM + быстрый расход) ---

    @bot.message_handler(content_types=["text"])
    def on_text(message: types.Message) -> None:
        if not message.text or message.text.startswith("/"):
            return

        chat_id = message.chat.id
        uid = user_id(message)
        text = message.text.strip()

        if text.lower() in _MENU_TEXT_ALIASES:
            send_menu(chat_id, uid)
            return

        st = state_db.get_state(uid)
        if st and st.state:
            try:
                _handle_fsm(chat_id, uid, st.state, text)
            except AppError as exc:
                friendly_error(chat_id, exc)
            return

        # Быстрый ввод расхода числом
        if not is_in_dialog(uid):
            try:
                amount = parse_positive_amount(text)
                preview = expense_svc.preview_expense(uid, amount)
                expense_svc.save_pending_expense(uid, preview)
                bot.send_message(
                    chat_id,
                    messages.expense_confirm_text(preview, expense_svc),
                    reply_markup=keyboards.expense_confirm_keyboard(),
                    parse_mode="Markdown",
                )
            except InvalidAmountError:
                bot.send_message(
                    chat_id,
                    "Не понял сообщение.\n"
                    "Отправьте /start для меню или число для учёта расхода.",
                    reply_markup=keyboards.main_menu_keyboard(),
                )
            except NoActiveTripError:
                bot.send_message(
                    chat_id,
                    messages.no_active_trip_text(),
                    reply_markup=keyboards.main_menu_keyboard(),
                )
            except AppError as exc:
                friendly_error(chat_id, exc)

    def _handle_fsm(chat_id: int, uid: int, state: str, text: str) -> None:
        if state == BotState.TRIP_HOME_COUNTRY.value:
            draft, manual = creation_svc.set_home_country(uid, text)
            if manual:
                bot.send_message(
                    chat_id,
                    "Не нашёл валюту для этой страны.\n"
                    "Введите код валюты (RUB, USD) или название страны ещё раз.",
                )
            else:
                bot.send_message(
                    chat_id,
                    f"Домашняя валюта: *{draft.home_currency}*\n\n"
                    "Введите *страну назначения*:",
                    parse_mode="Markdown",
                )

        elif state == BotState.TRIP_HOME_CURRENCY.value:
            draft = creation_svc.set_home_currency_manual(uid, text)
            bot.send_message(
                chat_id,
                f"Домашняя валюта: *{draft.home_currency}*\n\nВведите *страну назначения*:",
                parse_mode="Markdown",
            )

        elif state == BotState.TRIP_DESTINATION_COUNTRY.value:
            draft, manual = creation_svc.set_destination_country(uid, text)
            if manual:
                bot.send_message(
                    chat_id,
                    "Не нашёл валюту для этой страны.\n"
                    "Введите код валюты (USD, CNY) или название страны ещё раз.",
                )
            else:
                _show_rate_and_confirm(chat_id, uid, draft)

        elif state == BotState.TRIP_DESTINATION_CURRENCY.value:
            draft = creation_svc.set_destination_currency_manual(uid, text)
            _show_rate_and_confirm(chat_id, uid, draft)

        elif state == BotState.TRIP_RATE_MANUAL.value:
            draft = creation_svc.set_manual_rate(uid, text)
            bot.send_message(
                chat_id,
                f"Курс сохранён: 1 {draft.destination_currency} = "
                f"{format_amount(draft.rate)} {draft.home_currency}\n\n"
                f"Введите начальную сумму в {draft.home_currency}:",
            )

        elif state == BotState.TRIP_INITIAL_BALANCE.value:
            trip = creation_svc.complete_with_balance(uid, text)
            bot.send_message(
                chat_id,
                messages.trip_created_summary(trip, trip_svc),
                reply_markup=keyboards.main_menu_keyboard(),
                parse_mode="Markdown",
            )

        elif state == BotState.RATE_CHANGE_MANUAL.value:
            trip = rate_change_svc.apply_manual_rate(uid, text)
            dest = format_amount(trip.balance_destination)
            home = format_amount(trip.balance_home)
            bot.send_message(
                chat_id,
                f"Курс обновлён:\n{trip_svc.format_rate_line(trip)}\n\n"
                f"Остаток:\n{dest} {trip.destination_currency} = {home} {trip.home_currency}",
                reply_markup=keyboards.back_to_menu_keyboard(),
            )

        elif state == BotState.TRIP_RATE_CONFIRM.value:
            # Пользователь мог ввести курс текстом вместо кнопки
            try:
                draft = creation_svc.set_manual_rate(uid, text)
                bot.send_message(
                    chat_id,
                    f"Введите начальную сумму в {draft.home_currency}:",
                )
            except InvalidAmountError:
                bot.send_message(
                    chat_id,
                    "Используйте кнопки под сообщением с курсом или введите положительное число.",
                )

    def _show_rate_and_confirm(
        chat_id: int,
        uid: int,
        draft,
        *,
        force_refresh: bool = False,
    ) -> None:
        draft = creation_svc.get_draft(uid)
        try:
            rate_result = creation_svc.fetch_rate_for_draft(
                uid, force_refresh=force_refresh
            )
            creation_svc.set_draft_rate(uid, rate_result.rate, rate_result.source)
            draft = creation_svc.get_draft(uid)
            msg = (
                f"Валюта пребывания: *{draft.destination_currency}*\n\n"
                f"Текущий курс: 1 {draft.destination_currency} = "
                f"{format_amount(rate_result.rate)} {draft.home_currency}\n\n"
                "Подходит ли этот курс?"
            )
            if rate_result.warning:
                msg = f"⚠️ {rate_result.warning}\n\n" + msg
            bot.send_message(
                chat_id,
                msg,
                reply_markup=keyboards.rate_confirm_keyboard(),
                parse_mode="Markdown",
            )
        except CurrencyApiError:
            creation_svc.stay_on_rate_confirm(uid)
            draft = creation_svc.get_draft(uid)
            bot.send_message(
                chat_id,
                "Сейчас не получилось получить курс через API.\n"
                f"Пара: 1 {draft.destination_currency} = ? {draft.home_currency}\n\n"
                "Повторите запрос или введите курс вручную:",
                reply_markup=keyboards.rate_api_failed_keyboard(),
            )
