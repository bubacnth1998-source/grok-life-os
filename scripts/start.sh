#!/bin/bash
set -e
cd "$(dirname "$0")/.."
export PATH="${HOME}/.local/bin:${PATH}"
export PYTHONPATH="${PWD}/backend:${PYTHONPATH}"
mkdir -p data
export DATABASE_URL="${DATABASE_URL:-sqlite:///${PWD}/data/grok_life_os.db}"
export LIFE_OS_MEDIA_PATH="${LIFE_OS_MEDIA_PATH:-${PWD}/data/media}"
mkdir -p "$LIFE_OS_MEDIA_PATH"
PORT="${PORT:-8000}"
echo "Grok LIFE OS → http://127.0.0.1:${PORT}"
exec python3 -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port "$PORT"
