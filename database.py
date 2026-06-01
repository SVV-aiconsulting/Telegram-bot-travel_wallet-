"""
Универсальный модуль для работы с SQLite3.

Алгоритм подключения (кратко):
    1. Укажите путь к файлу базы — строкой или через pathlib.Path.
    2. Создайте экземпляр SQLiteDatabaseManager с этим путём.
    3. Вызовите connect() или используйте менеджер: ``with SQLiteDatabaseManager(...) as db:``.

Пример минимального использования см. в конце файла в блоке ``if __name__ == "__main__"``.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping, Optional, Sequence, Union

# Логгер модуля: сообщения попадут в корневой логгер, если настроен logging.basicConfig
logger = logging.getLogger(__name__)

# Типы для удобства: параметры запроса — кортеж, список или словарь (именованные плейсхолдеры)
SqlParams = Union[Sequence[Any], Mapping[str, Any]]


def _format_sql_for_log(sql: str, params: Optional[SqlParams]) -> str:
    """Собирает строку для лога: SQL и параметры (без маскировки — для обучения и отладки)."""
    if params is None or params == () or params == []:
        return sql.strip()
    return f"{sql.strip()} | параметры: {params!r}"


class SQLiteDatabaseManager:
    """
    Менеджер подключения к одной базе SQLite.

    Поддерживает контекстный менеджер: при входе подключается, при выходе — закрывает соединение.

    Параметры пути к базе (database_path) — пропишите своё значение:
        - Относительный путь к файлу в папке проекта:
          # Пример: база лежит рядом со скриптом
          SQLiteDatabaseManager("movies.db")
        - Абсолютный путь (Windows; можно обычные слэши / — SQLite их понимает):
          # Пример:
          # SQLiteDatabaseManager("D:/данные/my_app.sqlite")
          # Либо соберите путь через Path, чтобы не экранировать обратные слэши.
        - Через pathlib.Path:
          # Пример:
          # SQLiteDatabaseManager(Path(__file__).resolve().parent / "data" / "app.db")
        - База только в памяти (не сохраняется на диск после закрытия):
          # Пример:
          # SQLiteDatabaseManager(":memory:")
    """

    def __init__(
        self,
        database_path: Union[str, Path],
        *,
        detect_types: int = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        timeout: float = 5.0,
        isolation_level: Optional[str] = None,
        check_same_thread: bool = True,
    ) -> None:
        """
        Инициализация менеджера (соединение ещё не открыто, пока не вызван connect или ``with``).

        Args:
            database_path: Путь к файлу .db/.sqlite или ":memory:" (см. комментарии в классе).
            detect_types: Режим sqlite3 для типов колонок (по умолчанию как в sqlite3).
            timeout: Секунды ожидания блокировки файла БД.
            isolation_level: None — автокоммит после каждого execute; "DEFERRED" и др. — явные транзакции.
            check_same_thread: True — однопоточный режим. False — для Telegram/веб
                (несколько потоков); тогда запросы сериализуются внутренней блокировкой.
        """
        self._path = str(database_path) if isinstance(database_path, Path) else database_path
        self._detect_types = detect_types
        self._timeout = timeout
        self._isolation_level = isolation_level
        self._check_same_thread = check_same_thread
        # При доступе из разных потоков (pyTelegramBot) — общий RLock на все операции
        self._lock: Optional[threading.RLock] = (
            threading.RLock() if not check_same_thread else None
        )
        self._connection: Optional[sqlite3.Connection] = None
        logger.info(
            "Создан менеджер БД: путь=%r, timeout=%s, isolation_level=%r",
            self._path,
            self._timeout,
            self._isolation_level,
        )

    @property
    def database_path(self) -> str:
        """Текущий путь к базе (как передан при создании)."""
        return self._path

    @property
    def connection(self) -> sqlite3.Connection:
        """Активное соединение; вызовите connect() или используйте контекстный менеджер."""
        if self._connection is None:
            logger.error("Попытка доступа к connection без подключения")
            raise RuntimeError("Сначала вызовите connect() или используйте: with SQLiteDatabaseManager(...) as db:")
        return self._connection

    def __enter__(self) -> "SQLiteDatabaseManager":
        """Вход в контекст: подключение к базе."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Выход из контекста: отключение от базы."""
        self.disconnect()

    def connect(self) -> None:
        """
        Открыть соединение с SQLite.

        Если файл по пути не существует, SQLite создаст его при первой записи.
        """
        logger.info("Подключение к базе: %r", self._path)
        self._connection = sqlite3.connect(
            self._path,
            detect_types=self._detect_types,
            timeout=self._timeout,
            isolation_level=self._isolation_level,
            check_same_thread=self._check_same_thread,
        )
        # Удобство: строки по умолчанию как sqlite3.Row (доступ по имени колонки)
        self._connection.row_factory = sqlite3.Row
        logger.info("Подключение установлено, row_factory=sqlite3.Row")

    def disconnect(self) -> None:
        """Закрыть соединение с базой."""
        if self._connection is not None:
            logger.info("Отключение от базы: %r", self._path)
            self._connection.close()
            self._connection = None
        else:
            logger.debug("disconnect: соединение уже было закрыто или не открывалось")

    def is_connected(self) -> bool:
        """True, если соединение открыто."""
        return self._connection is not None

    @contextmanager
    def _synchronized(self) -> Iterator[None]:
        """Сериализует обращения к SQLite при check_same_thread=False."""
        if self._lock is None:
            yield
        else:
            with self._lock:
                yield

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Cursor]:
        """
        Контекстный менеджер транзакции: COMMIT при успехе, ROLLBACK при исключении.

        Пример:
            with db.transaction() as cur:
                cur.execute("INSERT INTO t (a) VALUES (?)", (1,))
                cur.execute("UPDATE t SET a = ? WHERE id = ?", (2, 1))

        Yields:
            Курсор соединения для execute внутри одной транзакции.
        """
        with self._synchronized():
            conn = self.connection
            logger.info("Начало транзакции (BEGIN)")
            try:
                cur = conn.cursor()
                yield cur
            except Exception:
                logger.exception("Ошибка в транзакции, выполняется ROLLBACK")
                conn.rollback()
                raise
            else:
                conn.commit()
                logger.info("Транзакция зафиксирована (COMMIT)")

    def execute(
        self,
        sql: str,
        parameters: Optional[SqlParams] = None,
        *,
        commit: bool = True,
    ) -> sqlite3.Cursor:
        """
        Выполнить один SQL-запрос (INSERT/UPDATE/DELETE/CREATE и т.д.).

        Args:
            sql: Текст запроса.
            parameters: Плейсхолдеры ? или именованные :name (словарь).
            commit: Если True и isolation_level=None — выполнить commit после запроса.
        """
        params = parameters if parameters is not None else ()
        with self._synchronized():
            logger.debug("execute: %s", _format_sql_for_log(sql, params))
            cur = self.connection.execute(sql, params)
            if commit and self._isolation_level is None:
                self.connection.commit()
                logger.debug("execute: commit выполнен")
            return cur

    def executemany(self, sql: str, seq_of_parameters: Sequence[SqlParams], *, commit: bool = True) -> sqlite3.Cursor:
        """
        Выполнить один запрос много раз с разными наборами параметров (пакетная вставка).
        """
        with self._synchronized():
            logger.debug("executemany: SQL=%s, число наборов параметров=%s", sql.strip(), len(seq_of_parameters))
            cur = self.connection.executemany(sql, seq_of_parameters)
            if commit and self._isolation_level is None:
                self.connection.commit()
                logger.debug("executemany: commit выполнен")
            return cur

    def execute_script(self, sql_script: str) -> None:
        """
        Выполнить скрипт из нескольких операторов (;), как в .sql файле.
        """
        with self._synchronized():
            logger.info("execute_script: длина скрипта=%s символов", len(sql_script))
            logger.debug("execute_script (начало): %s...", sql_script[:200].replace("\n", " "))
            self.connection.executescript(sql_script)
            if self._isolation_level is None:
                self.connection.commit()
            logger.info("execute_script завершён")

    def select_one(self, sql: str, parameters: Optional[SqlParams] = None) -> Optional[sqlite3.Row]:
        """
        Выполнить SELECT и вернуть одну строку (или None, если строк нет).

        Внутри используется cursor.fetchone() — имя метода отражает именно выборку из БД.
        """
        params = parameters if parameters is not None else ()
        with self._synchronized():
            logger.debug("select_one: %s", _format_sql_for_log(sql, params))
            cur = self.connection.execute(sql, params)
            row = cur.fetchone()
            logger.debug("select_one: получена строка=%s", row is not None)
            return row

    def select_all(self, sql: str, parameters: Optional[SqlParams] = None) -> list[sqlite3.Row]:
        """
        Выполнить SELECT и вернуть все строки списком.
        """
        params = parameters if parameters is not None else ()
        with self._synchronized():
            logger.debug("select_all: %s", _format_sql_for_log(sql, params))
            cur = self.connection.execute(sql, params)
            rows = cur.fetchall()
            logger.debug("select_all: число строк=%s", len(rows))
            return list(rows)

    def select_many(self, sql: str, parameters: Optional[SqlParams] = None, size: int = 100) -> list[sqlite3.Row]:
        """
        Выполнить SELECT и прочитать до ``size`` строк (порциями для больших таблиц).
        """
        params = parameters if parameters is not None else ()
        with self._synchronized():
            logger.debug("select_many: %s, size=%s", _format_sql_for_log(sql, params), size)
            cur = self.connection.execute(sql, params)
            rows = cur.fetchmany(size)
            logger.debug("select_many: получено строк=%s", len(rows))
            return list(rows)

    def insert(
        self,
        table: str,
        data: Mapping[str, Any],
        *,
        commit: bool = True,
    ) -> int:
        """
        Вставить одну строку в таблицу по словарю column -> value.

        Returns:
            lastrowid — идентификатор вставленной строки (для INTEGER PRIMARY KEY).
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        values = tuple(data.values())
        logger.info("insert в таблицу %s: %s", table, _format_sql_for_log(sql, values))
        cur = self.execute(sql, values, commit=commit)
        last_id = int(cur.lastrowid) if cur.lastrowid is not None else 0
        logger.debug("insert: lastrowid=%s", last_id)
        return last_id

    def update(
        self,
        table: str,
        data: Mapping[str, Any],
        where_clause: str,
        where_params: Optional[Sequence[Any]] = None,
        *,
        commit: bool = True,
    ) -> int:
        """
        Обновить строки в таблице.

        Args:
            table: Имя таблицы.
            data: Поля для обновления.
            where_clause: Условие без слова WHERE, например: "id = ?" или "name = :n".
            where_params: Параметры для условия (кортеж); если в data только именованные — согласуйте с SQL.

        Returns:
            rowcount — сколько строк затронуто.
        """
        set_part = ", ".join(f"{col} = ?" for col in data.keys())
        sql = f"UPDATE {table} SET {set_part} WHERE {where_clause}"
        values = tuple(data.values())
        wp: Sequence[Any] = where_params if where_params is not None else ()
        params: tuple[Any, ...] = values + tuple(wp)
        logger.info("update таблицы %s: %s", table, _format_sql_for_log(sql, params))
        cur = self.execute(sql, params, commit=commit)
        count = cur.rowcount
        logger.debug("update: rowcount=%s", count)
        return count

    def delete(
        self,
        table: str,
        where_clause: str,
        parameters: Optional[Sequence[Any]] = None,
        *,
        commit: bool = True,
    ) -> int:
        """
        Удалить строки по условию.

        Args:
            table: Имя таблицы.
            where_clause: Условие без WHERE, например: "id = ?".
            parameters: Значения для плейсхолдеров в условии.

        Returns:
            rowcount — сколько строк удалено.
        """
        params = tuple(parameters) if parameters is not None else ()
        sql = f"DELETE FROM {table} WHERE {where_clause}"
        logger.info("delete из %s: %s", table, _format_sql_for_log(sql, params))
        cur = self.execute(sql, params, commit=commit)
        count = cur.rowcount
        logger.debug("delete: rowcount=%s", count)
        return count

    def table_exists(self, table_name: str) -> bool:
        """Проверить, существует ли таблица в текущей базе (по sqlite_master)."""
        sql = "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1"
        logger.debug("table_exists: %s", table_name)
        row = self.select_one(sql, (table_name,))
        exists = row is not None
        logger.info("table_exists(%r) -> %s", table_name, exists)
        return exists

    def last_insert_row_id(self) -> int:
        """Последний ROWID после INSERT в этом соединении (через PRAGMA функции SQLite)."""
        with self._synchronized():
            rid = self.connection.execute("SELECT last_insert_rowid()").fetchone()[0]
            logger.debug("last_insert_rowid=%s", rid)
            return int(rid)

    def vacuum(self) -> None:
        """Сжать/оптимизировать файл базы (VACUUM)."""
        with self._synchronized():
            logger.info("VACUUM для %r", self._path)
            self.connection.execute("VACUUM")
            logger.info("VACUUM завершён")

    def pragma(self, name: str, value: Optional[Any] = None) -> Any:
        """
        Установить или прочитать PRAGMA.

        Пример чтения:
            db.pragma("user_version")  # только имя — вернёт значение через fetchone внутри.

        Пример записи:
            db.pragma("foreign_keys", 1)
        """
        if value is None:
            sql = f"PRAGMA {name}"
            logger.debug("pragma read: %s", sql)
            row = self.select_one(sql)
            result = row[0] if row is not None else None
            logger.info("pragma %s -> %r", name, result)
            return result
        sql = f"PRAGMA {name} = ?"
        logger.info("pragma set: %s значение=%r", sql, value)
        self.execute(sql, (value,))
        return None


if __name__ == "__main__":
    # Настройка логов в консоль, чтобы пример был наглядным
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s: %(message)s")

    # Путь к базе — ЗАМЕНИТЕ на свой при реальном использовании:
    # db_path = "my_database.sqlite"
    # db_path = r"C:\Users\Имя\Documents\app.db"
    # db_path = Path(__file__).resolve().parent / "example.sqlite"
    db_path = ":memory:"

    with SQLiteDatabaseManager(db_path) as db:
        db.execute_script(
            """
            CREATE TABLE demo (id INTEGER PRIMARY KEY, title TEXT NOT NULL);
            """
        )
        new_id = db.insert("demo", {"title": "Фильм 1"})
        db.update("demo", {"title": "Фильм 1 (ред.)"}, "id = ?", (new_id,))
        rows = db.select_all("SELECT * FROM demo")
        print("Строки:", [dict(r) for r in rows])
        db.delete("demo", "id = ?", (new_id,))
        print("После удаления:", db.select_all("SELECT * FROM demo"))
