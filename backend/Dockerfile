FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

# Shell form (not exec-form JSON array) so ${PORT} expands — Render and
# similar hosts inject PORT and expect the app to bind to it; falls back
# to 8000 for docker-compose / local runs where it isn't set.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
