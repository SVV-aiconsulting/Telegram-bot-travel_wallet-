#!/usr/bin/env bash
# Запуск бота с автоперезапуском при падении (Linux / VPS).
# Используется вручную или из systemd (см. deploy/travel-wallet-bot.service).

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PROJECT_ROOT}/venv/bin/python"
MAIN="${PROJECT_ROOT}/main.py"
LOG_DIR="${PROJECT_ROOT}/logs"
LOG_FILE="${LOG_DIR}/bot.log"
RESTART_DELAY=10

mkdir -p "$LOG_DIR"
cd "$PROJECT_ROOT"

if [[ ! -x "$PYTHON" ]]; then
  echo "Не найден venv: $PYTHON" >&2
  echo "Создайте: python3 -m venv venv && ./venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi

if [[ ! -f "${PROJECT_ROOT}/.env" ]]; then
  echo "Не найден .env в ${PROJECT_ROOT}" >&2
  exit 1
fi

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') $*" | tee -a "$LOG_FILE"
}

log "Старт run_bot.sh (каталог: $PROJECT_ROOT)"

while true; do
  log "Запуск: $PYTHON $MAIN"
  set +e
  "$PYTHON" "$MAIN" 2>&1 | tee -a "$LOG_FILE"
  exit_code=${PIPESTATUS[0]}
  set -e

  if [[ $exit_code -eq 0 ]]; then
    log "main.py завершился штатно (код 0). Выход."
    break
  fi

  log "main.py завершился с кодом $exit_code. Повтор через ${RESTART_DELAY} с..."
  sleep "$RESTART_DELAY"
done
