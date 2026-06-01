"""Слой доступа к состоянию диалога пользователя."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from database import SQLiteDatabaseManager
from domain.models import UserState


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _row_to_state(row) -> UserState:
    return UserState(
        telegram_user_id=row["telegram_user_id"],
        state=row["state"],
        payload_json=row["payload_json"],
        updated_at=row["updated_at"],
    )


class UserStateDatabase:
    """Хранение FSM-состояния в SQLite (переживает перезапуск бота)."""

    def __init__(self, db: SQLiteDatabaseManager) -> None:
        self._db = db

    def get_state(self, telegram_user_id: int) -> Optional[UserState]:
        row = self._db.select_one(
            "SELECT * FROM user_states WHERE telegram_user_id = ?",
            (telegram_user_id,),
        )
        return _row_to_state(row) if row else None

    def set_state(
        self,
        telegram_user_id: int,
        state: Optional[str],
        payload: Optional[dict[str, Any]] = None,
    ) -> None:
        payload_json = json.dumps(payload, ensure_ascii=False) if payload is not None else None
        now = _now_iso()
        existing = self.get_state(telegram_user_id)
        if existing:
            self._db.update(
                "user_states",
                {"state": state, "payload_json": payload_json, "updated_at": now},
                "telegram_user_id = ?",
                (telegram_user_id,),
            )
        else:
            self._db.insert(
                "user_states",
                {
                    "telegram_user_id": telegram_user_id,
                    "state": state,
                    "payload_json": payload_json,
                    "updated_at": now,
                },
            )

    def clear_state(self, telegram_user_id: int) -> None:
        self.set_state(telegram_user_id, None, None)

    def get_payload(self, telegram_user_id: int) -> dict[str, Any]:
        user_state = self.get_state(telegram_user_id)
        if not user_state or not user_state.payload_json:
            return {}
        try:
            return json.loads(user_state.payload_json)
        except json.JSONDecodeError:
            return {}

    def update_payload(self, telegram_user_id: int, payload: dict[str, Any]) -> None:
        current = self.get_state(telegram_user_id)
        self.set_state(
            telegram_user_id,
            current.state if current else None,
            payload,
        )
