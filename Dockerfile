# Telegram-бот «миникошелёк путешественника»
# Сборка: docker build -t travel-wallet-bot .
# Запуск:  docker run -d --name travel-wallet-bot \
#            -e TELEGRAM_BOT_TOKEN=... \
#            -e CURRENCY_API_KEY=... \
#            -v travel_wallet_data:/data \
#            travel-wallet-bot

FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/data/travel_wallet.sqlite3

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN adduser --disabled-password --gecos "" appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data

USER appuser

VOLUME ["/data"]

CMD ["python", "main.py"]
