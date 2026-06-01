# Миникошелёк путешественника

Учебный Telegram-бот на Python: учёт расходов в поездках с конвертацией валют. Пользователь создаёт путешествия, вводит расходы числом в валюте страны пребывания — бот пересчитывает в домашнюю валюту, ведёт баланс и историю.

Проект построен на **ООП и слоях**: Telegram-фронтенд, backend-сервисы, слой SQLite, низкоуровневый клиент API.

## Возможности

- Несколько путешествий на одного пользователя Telegram; переключение активного
- Удаление путешествия (с расходами) из раздела «Мои путешествия»
- Домашняя валюта и валюта пребывания; курс: **1 destination = X home**
- Курс с [exchangerate.host](https://exchangerate.host) (`/convert`), ручной ввод, кэш 24 часа
- При сбое API — кнопки «Повторить запрос» / «Ввести вручную»
- Справочник стран в SQLite (5 языков); общие валюты (EUR для Германии, Мальты и др.)
- Быстрый ввод расхода числом (`100`, `99.50`, `99,50`) с подтверждением
- Inline-меню и slash-команды; тексты `старт`, `меню` открывают главное меню
- Состояние диалога (создание поездки) в БД — переживает перезапуск бота
- Подсказки после создания поездки: как ввести сумму расхода

## Требования

- Python 3.10+
- Токен Telegram-бота ([@BotFather](https://t.me/BotFather))
- Ключ API [exchangerate.host](https://exchangerate.host)

## Конфигурация

Скопируйте `.env.example` в `.env`:

```env
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
CURRENCY_API_KEY=ключ_exchangerate_host
DATABASE_PATH=travel_wallet.sqlite3
```

| Переменная | Обязательна | Описание |
|------------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | да | Токен бота |
| `CURRENCY_API_KEY` | да | `access_key` для exchangerate.host |
| `DATABASE_PATH` | нет | Путь к файлу SQLite (по умолчанию `travel_wallet.sqlite3`) |

Загрузка: `config.load_config()` — без токена и ключа приложение не стартует (понятное сообщение об ошибке).

## Установка и запуск

```bash
python -m venv venv
```

**Windows:**

```powershell
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# отредактируйте .env
python main.py
```

**Linux / macOS:**

```bash
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

При первом запуске создаётся база, таблицы и **справочник стран/валют** (см. ниже).

### Фоновый режим и автоперезапуск процесса

```powershell
# Windows
.\scripts\run_bot.ps1
```

```bash
# Linux
chmod +x scripts/run_bot.sh
./scripts/run_bot.sh
```

Логи: `logs/bot.log`.

### Автозапуск после перезагрузки сервера

Данные в SQLite сохраняются. После перезагрузки ОС нужно снова поднять процесс бота.

**Windows** — PowerShell от администратора:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
cd "путь\к\API_currency_converter"
.\scripts\install_autostart_windows.ps1
```

Задача Планировщика: `TravelWalletTelegramBot`.

**Linux (VPS)** — отредактируйте пути в `deploy/travel-wallet-bot.service`, затем:

```bash
sudo cp deploy/travel-wallet-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now travel-wallet-bot
```

## Управление в Telegram

### Slash-команды

| Команда | Действие |
|---------|----------|
| `/start`, `/menu` | Главное меню |
| `/newtrip` | Создать путешествие |
| `/switch` | Мои путешествия |
| `/balance` | Баланс активного путешествия |
| `/history` | Последние 10 расходов |
| `/setrate` | Изменить курс |

Также работают сообщения: `старт`, `start`, `меню`, `menu`.

### Главное меню (inline)

- ➕ Создать новое путешествие
- 🧳 Мои путешествия
- 💰 Баланс
- 📜 История расходов
- 💱 Изменить курс
- 🏠 Главное меню (в подразделах)

### Создание путешествия

1. Страна отправления → валюта (справочник или код `RUB`, `USD`)
2. Страна назначения → валюта
3. Курс с API (`1 CNY = X RUB`) — подтвердить, ввести вручную или повторить API при ошибке
4. Начальная сумма в домашней валюте → баланс в обеих валютах

### Расходы

При активном путешествии отправьте **число** в чат (сумма в валюте пребывания) → подтверждение → списание с баланса. Допускается отрицательный остаток с предупреждением.

### Мои путешествия

Нажатие на поездку → карточка с кнопками:

- **Сделать активным**
- **Удалить путешествие** (с подтверждением, удаляются и расходы)

## API exchangerate.host

| Endpoint | Назначение в проекте |
|----------|----------------------|
| `GET /convert` | Рабочая конвертация и курс (`amount=1`, параметр `access_key`) |
| `GET /list` | Только при **инициализации справочника** валют в БД |

В runtime бота запросы курсов идут **только через `/convert`**. Кэшируется курс пары, не сумма.

### Кэширование (24 часа)

1. Запрос: `from`, `to`, `amount=1` → поле `result` — курс.
2. Сохранение в `rate_cache`.
3. Повтор в течение 24 ч — без вызова API.
4. Сбой API + старый кэш — использование с предупреждением; без кэша — ручной ввод или повтор.

### Формула курса

**1 единица валюты пребывания = X единиц домашней валюты**

- Расход: `сумма_дом = сумма_пребывания × курс`
- Стартовый баланс: `баланс_пребывания = сумма_дом / курс`
- Смена курса: баланс в валюте пребывания фиксирован, домашний пересчитывается

## Справочник стран и валют

Таблицы (создаются при старте, данные в `data/country_names_seed.py`):

| Таблица | Содержимое |
|---------|------------|
| `supported_currencies` | Коды валют с `/list` API (+ резервный список) |
| `country_currency_names` | Название страны → `currency_code`, языки **en, ru, es, fr, de** |

Для **EUR** перечислены страны еврозоны (Германия, Мальта, Франция, …) — одна валюта на много стран.

Поиск: `CountryResolverService` (страна или код `USD`).

Обновить справочник после правок в seed-файле:

```bash
python scripts/reseed_country_reference.py
```

## База данных SQLite

Файл задаётся в `DATABASE_PATH` (по умолчанию `travel_wallet.sqlite3`).

| Таблица | Назначение |
|---------|------------|
| `trips` | Путешествия, баланс, курс, активное |
| `expenses` | История расходов |
| `rate_cache` | Кэш курсов валютных пар |
| `user_states` | FSM и черновики (pending-расход) |
| `supported_currencies` | Справочник кодов валют |
| `country_currency_names` | Справочник стран → валюта |

Низкоуровневый доступ: `database.py` → класс `SQLiteDatabaseManager` (не менять под бизнес-логику).

## Структура проекта

```text
API_currency_converter/
├── main.py                      # Точка входа, infinity_polling
├── config.py                    # AppConfig из .env
├── container.py                 # DI: create_container()
├── database.py                  # Универсальный SQLiteDatabaseManager
├── currency_manager.py          # HTTP: /convert и /list (для справочника)
├── country_currency.py          # Устаревшие хелперы (используйте resolver)
│
├── data/                        # Статические данные для заполнения БД
│   ├── __init__.py              # Пакет data
│   └── country_names_seed.py    # Названия стран (5 языков) → валюта
│
├── domain/                      # Модели, DTO, ошибки, утилиты (без Telegram и SQL)
│   ├── models.py                # Trip, Expense, RateCacheEntry, UserState
│   ├── dto.py                   # DTO для обмена между слоями
│   ├── errors.py                # CurrencyApiError, TripNotFoundError, …
│   ├── number_utils.py          # Парсинг и формат денежных сумм
│   ├── states.py                # Имена FSM-состояний (BotState)
│   └── text_normalize.py        # Нормализация текста для поиска в справочнике
│
├── database_layer/              # SQL-репозитории поверх database.py
│   ├── schema.py                # Таблицы: trips, expenses, rate_cache, user_states
│   ├── reference_schema.py      # Таблицы: supported_currencies, country_currency_names
│   ├── reference_seed.py        # Заполнение справочника при старте (/list + seed)
│   ├── trip_database.py         # CRUD путешествий
│   ├── expense_database.py      # CRUD расходов
│   ├── rate_cache_database.py   # CRUD кэша курсов
│   ├── user_state_database.py   # FSM и payload_json в SQLite
│   └── country_currency_database.py  # Поиск страны → код валюты
│
├── services/                    # Бизнес-логика (без Telegram)
│   ├── trip_service.py          # Путешествия, баланс, удаление, смена активного
│   ├── expense_service.py       # Расходы, предпросмотр, подтверждение
│   ├── currency_service.py      # Курс через API + кэш 24 ч
│   ├── country_resolver_service.py  # Страна или код → валюта (справочник БД)
│   ├── creation_service.py      # Сценарий создания путешествия (черновик FSM)
│   └── rate_change_service.py   # Смена курса активного путешествия
│
├── bot/                         # Telegram-фронтенд
│   ├── handlers.py              # Команды, callback, текстовые сообщения
│   ├── keyboards.py             # Inline-клавиатуры
│   ├── messages.py              # Тексты ответов и подсказки
│   └── states.py                # Реэкспорт domain.states для bot/
│
├── scripts/                     # Служебные скрипты запуска и обслуживания
│   ├── run_bot.ps1              # Windows: запуск с автоперезапуском
│   ├── run_bot.sh               # Linux: запуск с автоперезапуском
│   ├── install_autostart_windows.ps1  # Автозапуск через Планировщик Windows
│   └── reseed_country_reference.py    # Перезаполнить справочник стран
│
├── deploy/                      # Развёртывание на сервере
│   └── travel-wallet-bot.service  # Unit systemd для Linux VPS
│
├── logs/                        # Логи run_bot.* (bot.log)
├── requirements.txt             # Зависимости Python
├── .env.example                 # Шаблон переменных окружения
├── .env                         # Локальные секреты (не коммитить)
└── README.md                    # Документация проекта
```

## Архитектура слоёв

```text
Telegram (bot/)  →  services/  →  database_layer/  →  database.py
                           ↓
                  currency_manager.py  →  exchangerate.host
```

| Слой | Ответственность | Не делает |
|------|-----------------|-----------|
| `bot/` | Сообщения, кнопки, вызов сервисов | SQL, расчёты, HTTP к API |
| `services/` | Бизнес-логика, DTO | Telegram, прямой SQL |
| `database_layer/` | SQL, модели из БД | Telegram, формулы |
| `currency_manager.py` | Только HTTP API | Путешествия, SQLite |
| `database.py` | Универсальный SQLite | Доменная логика |

Сборка зависимостей:

```python
from config import load_config
from container import create_container

config = load_config()
container = create_container(config)

# Примеры
trip = container.trip_service.get_active_trip(telegram_user_id=123)
currency = container.country_resolver.lookup_currency_by_country("Мальта")  # EUR
```

Другой frontend (CLI, Web) подключается через тот же `create_container()` — без дублирования логики в обработчиках.

## Зависимости

```text
pytelegrambotapi   # Telegram Bot API
requests           # HTTP к exchangerate.host
python-dotenv      # Переменные из .env
```

## Скрипты обслуживания

| Скрипт | Назначение |
|--------|------------|
| `scripts/reseed_country_reference.py` | Перезаполнить справочник стран |
| `scripts/run_bot.ps1` / `run_bot.sh` | Запуск с автоперезапуском при падении |
| `scripts/install_autostart_windows.ps1` | Автозапуск в Windows |

## Устранение неполадок

| Симптом | Что проверить |
|---------|----------------|
| Бот молчит на сообщения | Запущен ли `python main.py`; в логе нет ошибок SQLite/потоков |
| «Не нашёл валюту» для известной страны | `python scripts/reseed_country_reference.py` |
| Ошибка API курса | Ключ в `.env`, лимиты exchangerate.host; кнопка «Повторить» |
| Старая база без справочника | Перезапуск бота (справочник заполнится, если таблица пуста) |

---

Учебный проект ZEROCODER. Код с docstring на русском в ключевых модулях.
