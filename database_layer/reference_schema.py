"""Схема справочника стран и валют (exchangerate.host)."""

from __future__ import annotations

from database import SQLiteDatabaseManager

REFERENCE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS supported_currencies (
    code TEXT PRIMARY KEY,
    source TEXT NOT NULL DEFAULT 'seed',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS country_currency_names (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    currency_code TEXT NOT NULL,
    country_name TEXT NOT NULL,
    name_normalized TEXT NOT NULL,
    language_code TEXT NOT NULL,
    FOREIGN KEY (currency_code) REFERENCES supported_currencies(code),
    UNIQUE(name_normalized)
);

CREATE INDEX IF NOT EXISTS idx_country_name_norm ON country_currency_names(name_normalized);
CREATE INDEX IF NOT EXISTS idx_country_currency ON country_currency_names(currency_code);
"""


def init_reference_schema(db: SQLiteDatabaseManager) -> None:
    """Создаёт таблицы справочника."""
    db.execute_script(REFERENCE_SCHEMA_SQL)
