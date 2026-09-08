#!/bin/bash
set -euo pipefail

PORT="${PORT:-8000}"
ENVIRONMENT="${ENVIRONMENT:-${FASTAPI_ENV:-development}}"

echo "Running database migrations..."
python -m alembic upgrade head

echo "Starting QuizNess API on port ${PORT}..."
if [ "${ENVIRONMENT}" = "production" ]; then
  exec uvicorn main:app --host 0.0.0.0 --port "${PORT}"
fi

exec uvicorn main:app --host 0.0.0.0 --port "${PORT}" --reload
