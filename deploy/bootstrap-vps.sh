#!/usr/bin/env bash
# Одноразовая подготовка VPS перед автодеплоем из GitHub Actions.
#
# Запуск на сервере (после установки git и Docker):
#   chmod +x deploy/bootstrap-vps.sh
#   ./deploy/bootstrap-vps.sh
#
# Скрипт клонирует репозиторий (если ещё нет) и создаёт .env из шаблона.
# Секреты вводите вручную в .env — файл не попадает в git и не перезаписывается при деплое.

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/SVV-aiconsulting/Telegram-bot-travel_wallet-.git}"
DEPLOY_PATH="${DEPLOY_PATH:-$HOME/travel-wallet-bot}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker не найден. Установите Docker и docker compose plugin на VPS." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose plugin не найден." >&2
  exit 1
fi

if [[ ! -d "$DEPLOY_PATH/.git" ]]; then
  echo "Клонирование в $DEPLOY_PATH ..."
  git clone "$REPO_URL" "$DEPLOY_PATH"
fi

cd "$DEPLOY_PATH"

if [[ ! -f .env ]]; then
  cp .env.example .env
  chmod 600 .env
  echo ""
  echo "Создан $DEPLOY_PATH/.env — заполните секреты:"
  echo "  nano .env"
  echo ""
  echo "Обязательные переменные:"
  echo "  TELEGRAM_BOT_TOKEN"
  echo "  CURRENCY_API_KEY"
  echo ""
  echo "После сохранения .env запустите снова:"
  echo "  ./deploy/bootstrap-vps.sh"
  exit 0
fi

chmod 600 .env

docker compose build
docker compose up -d

echo ""
echo "Бот запущен. Логи: docker compose logs -f bot"
echo "Путь деплоя для GitHub Secret VPS_DEPLOY_PATH: $DEPLOY_PATH"
