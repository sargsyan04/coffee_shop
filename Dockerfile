FROM python:3.12-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


FROM base AS test

COPY . .

ENV SECRET_KEY=test-secret-key-for-ci \
    DB_HOST=localhost \
    DB_PASSWORD=test \
    DB_NAME=test \
    MAIL_FROM=test@example.com

RUN pytest tests/ -q

FROM base AS production

COPY src ./src
COPY frontend ./frontend
COPY migrations ./migrations
COPY alembic.ini .

EXPOSE 8080

CMD ["sh", "-c", "alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8080"]
