"""Парсинг и форматирование денежных сумм."""

from __future__ import annotations

import re

from domain.errors import InvalidAmountError

# Допустимы целые и дробные числа с точкой или запятой
_AMOUNT_PATTERN = re.compile(r"^\s*(\d+)(?:[.,](\d+))?\s*$")


def parse_positive_amount(text: str) -> float:
    """
    Преобразует строку в положительное число.

    Принимает: 100, 100.50, 100,50
    Не принимает: отрицательные, ноль, текст, пустые строки.
    """
    if not text or not str(text).strip():
        raise InvalidAmountError("Пустая строка")

    match = _AMOUNT_PATTERN.match(str(text).strip())
    if not match:
        raise InvalidAmountError("Не удалось распознать число")

    integer_part = match.group(1)
    fractional_part = match.group(2) or ""
    value = float(f"{integer_part}.{fractional_part}" if fractional_part else integer_part)

    if value <= 0:
        raise InvalidAmountError("Сумма должна быть больше нуля")

    return value


def format_amount(value: float, max_decimals: int = 2) -> str:
    """
    Форматирует число для вывода: до 2 знаков, без лишних нулей.

    Примеры: 1280 -> "1280", 12.8 -> "12.8", 99.5 -> "99.5"
    """
    rounded = round(value, max_decimals)
    if rounded == int(rounded):
        return str(int(rounded))
    text = f"{rounded:.{max_decimals}f}".rstrip("0").rstrip(".")
    return text
