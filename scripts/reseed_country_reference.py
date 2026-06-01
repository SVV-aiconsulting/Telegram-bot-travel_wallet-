#!/usr/bin/env python
"""
Перезаполнить справочник стран и валют (после обновления data/country_names_seed.py).

Запуск из корня проекта:
    python scripts/reseed_country_reference.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import load_config
from database import SQLiteDatabaseManager
from database_layer.reference_seed import ensure_country_currency_reference


def main() -> None:
    config = load_config()
    db = SQLiteDatabaseManager(config.database_path, check_same_thread=False)
    db.connect()
    ensure_country_currency_reference(
        db, config.currency_api_key, force_reseed=True
    )
    db.disconnect()
    print("Справочник стран и валют обновлён.")


if __name__ == "__main__":
    main()
