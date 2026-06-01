"""
Сборка зависимостей приложения (DI-контейнер).

Все фронтенды (Telegram, CLI, Web) должны использовать один backend через этот контейнер.
"""

from __future__ import annotations

from dataclasses import dataclass

from config import AppConfig
from currency_manager import ExchangeRateClient
from database import SQLiteDatabaseManager
from database_layer.expense_database import ExpenseDatabase
from database_layer.rate_cache_database import RateCacheDatabase
from database_layer.country_currency_database import CountryCurrencyDatabase
from database_layer.reference_seed import ensure_country_currency_reference
from database_layer.schema import init_database_schema
from database_layer.trip_database import TripDatabase
from database_layer.user_state_database import UserStateDatabase
from services.country_resolver_service import CountryResolverService
from services.creation_service import CreationService
from services.currency_service import CurrencyService
from services.expense_service import ExpenseService
from services.rate_change_service import RateChangeService
from services.trip_service import TripService


@dataclass
class AppContainer:
    """Контейнер со всеми сервисами backend."""

    config: AppConfig
    db: SQLiteDatabaseManager
    trip_service: TripService
    expense_service: ExpenseService
    currency_service: CurrencyService
    creation_service: CreationService
    rate_change_service: RateChangeService
    user_state_db: UserStateDatabase
    country_resolver: CountryResolverService


def create_container(config: AppConfig) -> AppContainer:
    """Создаёт подключение к БД, инициализирует схему и сервисы."""
    # check_same_thread=False: pyTelegramBot обрабатывает сообщения в пуле потоков
    db = SQLiteDatabaseManager(config.database_path, check_same_thread=False)
    db.connect()
    init_database_schema(db)
    ensure_country_currency_reference(db, config.currency_api_key)

    country_currency_db = CountryCurrencyDatabase(db)
    country_resolver = CountryResolverService(country_currency_db)

    trip_db = TripDatabase(db)
    expense_db = ExpenseDatabase(db)
    rate_cache_db = RateCacheDatabase(db)
    user_state_db = UserStateDatabase(db)

    api_client = ExchangeRateClient(config.currency_api_key)
    currency_service = CurrencyService(api_client, rate_cache_db)
    trip_service = TripService(
        trip_db, expense_db, currency_service, user_state_db, country_resolver
    )
    expense_service = ExpenseService(expense_db, trip_db, trip_service, user_state_db)
    creation_service = CreationService(
        user_state_db, trip_service, currency_service, country_resolver
    )
    rate_change_service = RateChangeService(trip_service, user_state_db)

    return AppContainer(
        config=config,
        db=db,
        trip_service=trip_service,
        expense_service=expense_service,
        currency_service=currency_service,
        creation_service=creation_service,
        rate_change_service=rate_change_service,
        user_state_db=user_state_db,
        country_resolver=country_resolver,
    )
