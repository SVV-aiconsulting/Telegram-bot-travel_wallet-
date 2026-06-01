"""Инициализация схемы SQLite для миникошелька путешественника."""

from __future__ import annotations

from database import SQLiteDatabaseManager

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    home_country TEXT,
    destination_country TEXT,
    home_currency TEXT NOT NULL,
    destination_currency TEXT NOT NULL,
    rate REAL NOT NULL,
    rate_source TEXT NOT NULL,
    balance_home REAL NOT NULL,
    balance_destination REAL NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER NOT NULL,
    telegram_user_id INTEGER NOT NULL,
    amount_destination REAL NOT NULL,
    amount_home REAL NOT NULL,
    rate REAL NOT NULL,
    created_at TEXT NOT NULL,
    comment TEXT,
    FOREIGN KEY (trip_id) REFERENCES trips(id)
);

CREATE TABLE IF NOT EXISTS rate_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_currency TEXT NOT NULL,
    to_currency TEXT NOT NULL,
    rate REAL NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(from_currency, to_currency)
);

CREATE TABLE IF NOT EXISTS user_states (
    telegram_user_id INTEGER PRIMARY KEY,
    state TEXT,
    payload_json TEXT,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_trips_user ON trips(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_expenses_trip ON expenses(trip_id);
CREATE INDEX IF NOT EXISTS idx_expenses_user ON expenses(telegram_user_id);
"""


def init_database_schema(db: SQLiteDatabaseManager) -> None:
    """Создаёт таблицы, если их ещё нет."""
    db.execute_script(SCHEMA_SQL)
