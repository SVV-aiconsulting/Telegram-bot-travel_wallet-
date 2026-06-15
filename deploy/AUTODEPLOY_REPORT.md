# Отчёт: автодеплой Telegram-бота через GitHub Actions

Краткое описание настройки CI/CD для проекта **Travel Wallet Bot** (VPS Beget, Docker).

Бот активен для проверки и теста: @MyTravelWallet_bot

---

## Цель

Автоматически обновлять бота на VPS при merge изменений в ветку `main`: код с GitHub → **сборка Docker-образа в GitHub Actions** → публикация в **GitHub Container Registry (GHCR)** → на VPS только `docker compose pull` и перезапуск. Сборка на слабом VPS не выполняется. Секреты бота (`.env`) хранятся только на сервере, не в репозитории.

---

## Добавленные файлы в репозитории

| Файл | Назначение |
|------|------------|
| `Dockerfile` | Образ Python 3.12, запуск `main.py` |
| `.dockerignore` | Исключение `.env`, БД, venv из образа |
| `docker-compose.yml` | Сервис бота, volume для SQLite, `env_file: .env` |
| `.github/workflows/deploy.yml` | Сборка образа в Actions, push в GHCR, деплой на VPS |
| `deploy/bootstrap-vps.sh` | Одноразовая подготовка VPS (клон + шаблон `.env`) |

---

## Ветки и слияния

Работа велась по схеме **feature → main** (два этапа изменений):

### 1. Ветка `feature` — базовая инфраструктура деплоя

- Docker, docker-compose, GitHub Actions workflow.
- Merge в `main` (Pull Request #1).
- Первый запуск Actions выявил ошибки конфигурации.

### 2. Ветка `feature` — исправление workflow

- В `.github/workflows/deploy.yml`:
  - `port: 22` вместо secret `VPS_PORT` (избежание ошибки парсинга порта).
  - удалён неподдерживаемый параметр `script_stop`.
- Merge в `main` (Pull Request #2).
- Деплой прошёл успешно.

---

## SSH-ключи для GitHub Actions

Для деплоя создан **отдельный** ключ (не личный ключ пользователя):

| Компонент | Расположение |
|-----------|--------------|
| Приватный ключ | GitHub Secret `VPS_SSH_PRIVATE_KEY` |
| Публичный ключ | VPS: `/root/.ssh/authorized_keys` |
| Файлы на ПК | `C:\Users\user\.ssh\deploy_travel_bot` и `.pub` |

**Требования к ключу для CI:**

- алгоритм `ed25519`;
- **без passphrase** (иначе Actions не сможет подключиться);
- публичный ключ — только на VPS, приватный — только в GitHub Secrets.

---

## GitHub Secrets

| Secret | Пример / описание |
|--------|-------------------|
| `VPS_HOST` | IP VPS (`62.113.103.96`) |
| `VPS_USER` | `root` |
| `VPS_DEPLOY_PATH` | `/root/travel-wallet-bot` |
| `VPS_SSH_PRIVATE_KEY` | содержимое `deploy_travel_bot` (приватный ключ) |

Secret `VPS_PORT` после правки workflow **не используется** (порт задан в файле: `22`).

Секреты бота (`TELEGRAM_BOT_TOKEN`, `CURRENCY_API_KEY`) в GitHub **не хранятся** — только в `.env` на VPS.

---

## Настройка VPS (один раз)

1. Установлены: git, Docker, Docker Compose.
2. Клон репозитория: `/root/travel-wallet-bot` (ветка `feature`, затем синхронизация с `main` через Actions).
3. Файл `.env` загружен на сервер вручную (через файловый менеджер Beget).
4. Первый ручной запуск: `docker compose pull && docker compose up -d` (образ уже должен быть в GHCR после merge в `main`).
5. База SQLite — в Docker volume `travel_wallet_data`.

---

## GitHub Container Registry (GHCR)

Образ публикуется в реестр GitHub (как в учебном задании):

| Параметр | Значение |
|----------|----------|
| Реестр | `ghcr.io` |
| Образ | `ghcr.io/svv-aiconsulting/travel-wallet-bot` |
| Теги | `latest`, `<commit-sha>` |

Сборка выполняется на runner GitHub Actions (`ubuntu-latest`), не на VPS.

**Доступ к образу на VPS:**

- Если пакет **публичный** — `docker compose pull` работает без логина.
- Если пакет **приватный** — один раз на VPS: `docker login ghcr.io` (PAT с `read:packages`), либо добавить GitHub Secret `GHCR_PULL_TOKEN` (workflow выполнит login перед pull).

Сделать пакет публичным: GitHub → **Packages** → `travel-wallet-bot` → **Package settings** → **Change visibility**.

## Как работает автодеплой

```
push / merge в main
       ↓
GitHub Actions: job build-and-push
       ↓
docker build → push в ghcr.io/svv-aiconsulting/travel-wallet-bot
       ↓
GitHub Actions: job deploy (appleboy/ssh-action)
       ↓
SSH → VPS → cd /root/travel-wallet-bot
       ↓
git fetch + git reset --hard origin/main
       ↓
docker compose pull && docker compose up -d
```

Файл `.env` при деплое **не перезаписывается** (не в git).

---

## Устранённые проблемы при настройке

| Проблема | Решение |
|----------|---------|
| `VPS_PORT` — invalid syntax | Порт `22` прописан в workflow |
| `script_stop` — unexpected input | Параметр удалён из workflow |
| `private key is passphrase protected` | Пересоздан ключ без passphrase, обновлены Secret и `authorized_keys` |

---

## Текущий статус

- ✅ Бот работает на VPS в Docker.
- ✅ Автодеплой при merge в `main` выполняется успешно.
- ✅ Секреты бота изолированы в `.env` на сервере.
- ✅ Образ собирается в GitHub Actions и публикуется в GHCR (VPS только скачивает готовый образ).

**Дата настройки:** июнь 2026.
