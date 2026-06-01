"""
Бизнес-сервис курсов валют: кэш 24 часа, fallback на старый кэш при сбое API.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from domain.text_normalize import normalize_currency_code
from currency_manager import ExchangeRateClient
from database_layer.rate_cache_database import RateCacheDatabase
from domain.dto import RateResult
from domain.errors import CurrencyApiError, CurrencyNotFoundError

logger = logging.getLogger(__name__)

CACHE_TTL = timedelta(hours=24)


class CurrencyService:
    """Получение и кэширование курса: 1 from_currency = rate to_currency."""

    def __init__(
        self,
        api_client: ExchangeRateClient,
        rate_cache_db: RateCacheDatabase,
    ) -> None:
        self._api = api_client
        self._cache = rate_cache_db

    def get_exchange_rate(
        self,
        from_currency: str,
        to_currency: str,
        *,
        force_refresh: bool = False,
    ) -> RateResult:
        """
        Возвращает курс: 1 from = rate to.

        Сначала проверяет кэш (< 24 ч), затем API. При сбое API — старый кэш с предупреждением.
        """
        fc = normalize_currency_code(from_currency)
        tc = normalize_currency_code(to_currency)

        if fc == tc:
            return RateResult(from_currency=fc, to_currency=tc, rate=1.0, source="cache")

        if not self._is_iso_currency_code(fc) or not self._is_iso_currency_code(tc):
            raise CurrencyNotFoundError("Некорректный код валюты")

        cached = self._cache.get_rate(fc, tc)
        if cached and not force_refresh and self._is_fresh(cached.updated_at):
            return RateResult(
                from_currency=fc,
                to_currency=tc,
                rate=cached.rate,
                source="cache",
            )

        if force_refresh or not cached or not self._is_fresh(cached.updated_at if cached else ""):
            return self._fetch_and_cache(fc, tc, cached)

        return RateResult(
            from_currency=fc,
            to_currency=tc,
            rate=cached.rate,
            source="cache",
        )

    def validate_currency_pair(self, from_currency: str, to_currency: str) -> RateResult:
        """Проверяет пару валют через API (с учётом кэша)."""
        return self.get_exchange_rate(from_currency, to_currency)

    def set_manual_rate(self, from_currency: str, to_currency: str, rate: float) -> RateResult:
        """Сохраняет курс, введённый пользователем, в кэш."""
        if rate <= 0:
            raise CurrencyNotFoundError("Курс должен быть положительным")
        fc = normalize_currency_code(from_currency)
        tc = normalize_currency_code(to_currency)
        self._cache.upsert_rate(fc, tc, rate)
        return RateResult(from_currency=fc, to_currency=tc, rate=rate, source="manual")

    def _fetch_and_cache(self, fc: str, tc: str, stale_cache) -> RateResult:
        try:
            rate = self._api.get_rate(fc, tc)
            self._cache.upsert_rate(fc, tc, rate)
            return RateResult(from_currency=fc, to_currency=tc, rate=rate, source="api")
        except (CurrencyApiError, CurrencyNotFoundError) as exc:
            if stale_cache:
                warning = (
                    "Сейчас не получилось обновить курс через API. "
                    "Использую последний сохранённый курс."
                )
                logger.warning("%s: %s", warning, exc.message)
                return RateResult(
                    from_currency=fc,
                    to_currency=tc,
                    rate=stale_cache.rate,
                    source="cache",
                    stale=True,
                    warning=warning,
                )
            raise

    @staticmethod
    def _is_iso_currency_code(code: str) -> bool:
        return len(code) == 3 and code.isascii() and code.isalpha()

    @staticmethod
    def _is_fresh(updated_at: str) -> bool:
        try:
            updated = datetime.strptime(updated_at, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            return False
        return datetime.now(timezone.utc) - updated < CACHE_TTL
