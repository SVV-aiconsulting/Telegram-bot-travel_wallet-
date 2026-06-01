"""
Низкоуровневый клиент API exchangerate.host.

Использует только endpoint /convert. Не знает о путешествиях, Telegram и SQLite.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

import requests

from domain.errors import CurrencyApiError, CurrencyNotFoundError

logger = logging.getLogger(__name__)

CONVERT_URL = "https://api.exchangerate.host/convert"
LIST_URL = "https://api.exchangerate.host/list"
DEFAULT_TIMEOUT = 10


@dataclass
class ConvertResult:
    """Результат конвертации от API."""

    from_currency: str
    to_currency: str
    amount: float
    result: float
    success: bool
    raw: dict[str, Any]


class ExchangeRateClient:
    """HTTP-клиент для https://api.exchangerate.host/convert."""

    def __init__(self, access_key: str, timeout: float = DEFAULT_TIMEOUT) -> None:
        self._access_key = access_key
        self._timeout = timeout

    def convert(
        self,
        from_currency: str,
        to_currency: str,
        amount: float = 1.0,
    ) -> ConvertResult:
        """
        Выполняет конвертацию через API.

        Args:
            from_currency: Исходная валюта (например CNY).
            to_currency: Целевая валюта (например RUB).
            amount: Сумма для конвертации (для курса используйте 1).

        Returns:
            ConvertResult с полем result — итоговая сумма в to_currency.
        """
        params = {
            "access_key": self._access_key,
            "from": from_currency.upper(),
            "to": to_currency.upper(),
            "amount": amount,
        }
        try:
            response = requests.get(CONVERT_URL, params=params, timeout=self._timeout)
            response.raise_for_status()
            data = response.json()
        except requests.Timeout as exc:
            logger.exception("Таймаут API exchangerate.host")
            raise CurrencyApiError("Превышено время ожидания ответа API") from exc
        except requests.RequestException as exc:
            logger.exception("Сетевая ошибка API exchangerate.host")
            raise CurrencyApiError("Не удалось связаться с API курсов валют") from exc

        return self._parse_response(data, from_currency, to_currency, amount)

    def _parse_response(
        self,
        data: dict[str, Any],
        from_currency: str,
        to_currency: str,
        amount: float,
    ) -> ConvertResult:
        """Разбирает JSON-ответ API."""
        if not data.get("success", False):
            error_info = data.get("error") or data.get("message") or "неизвестная ошибка"
            raise CurrencyApiError(f"API вернул ошибку: {error_info}")

        result_info = data.get("result")
        if result_info is None:
            raise CurrencyNotFoundError("В ответе API нет поля result")

        try:
            result_value = float(result_info)
        except (TypeError, ValueError) as exc:
            raise CurrencyApiError("Некорректное значение result в ответе API") from exc

        if result_value <= 0:
            raise CurrencyNotFoundError("Курс должен быть положительным числом")

        info = data.get("info") or {}
        query = data.get("query") or {}

        fc = (info.get("from") or query.get("from") or from_currency).upper()
        tc = (info.get("to") or query.get("to") or to_currency).upper()

        return ConvertResult(
            from_currency=fc,
            to_currency=tc,
            amount=amount,
            result=result_value,
            success=True,
            raw=data,
        )

    def get_rate(self, from_currency: str, to_currency: str) -> float:
        """
        Возвращает курс: сколько to_currency за 1 from_currency.

        Эквивалентно convert с amount=1 и полем result.
        """
        converted = self.convert(from_currency, to_currency, amount=1.0)
        return converted.result

    def fetch_supported_currency_codes(self) -> list[str]:
        """
        Загружает коды валют с https://api.exchangerate.host/list.

        Используется только при заполнении справочника в БД, не в runtime-конвертации.
        """
        try:
            response = requests.get(
                LIST_URL,
                params={"access_key": self._access_key},
                timeout=self._timeout,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise CurrencyApiError("Не удалось получить список валют с API") from exc

        if not data.get("success", False):
            error_info = data.get("error") or data.get("message") or "неизвестная ошибка"
            raise CurrencyApiError(f"API /list вернул ошибку: {error_info}")

        currencies = data.get("currencies")
        if isinstance(currencies, dict):
            return sorted(code.upper() for code in currencies.keys() if code)

        symbols = data.get("symbols")
        if isinstance(symbols, dict):
            return sorted(code.upper() for code in symbols.keys() if code)

        raise CurrencyApiError("В ответе /list нет поля currencies")


def get_all_supported_currencies(access_key: str) -> dict[str, Any]:
    """Обёртка для скриптов: полный ответ API /list."""
    client = ExchangeRateClient(access_key)
    codes = client.fetch_supported_currency_codes()
    return {"success": True, "currencies": {c: c for c in codes}}


# Обратная совместимость: функции-обёртки для простых скриптов
def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
    access_key: Optional[str] = None,
) -> dict[str, Any]:
    """Устаревшая функция-обёртка; предпочтительно ExchangeRateClient."""
    import os

    key = access_key or os.getenv("CURRENCY_API_KEY", "")
    client = ExchangeRateClient(key)
    result = client.convert(from_currency, to_currency, amount)
    return result.raw
