"""Доменные исключения backend-слоя (без привязки к Telegram)."""


class AppError(Exception):
    """Базовое исключение приложения."""

    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(message)


class CurrencyApiError(AppError):
    """Ошибка при обращении к валютному API."""


class CurrencyNotFoundError(AppError):
    """Валютная пара не найдена или код валюты неверен."""


class TripNotFoundError(AppError):
    """Путешествие не найдено."""


class NoActiveTripError(AppError):
    """У пользователя нет активного путешествия."""


class InvalidAmountError(AppError):
    """Некорректная сумма (не число, ноль, отрицательное)."""


class DatabaseError(AppError):
    """Ошибка при работе с базой данных."""
