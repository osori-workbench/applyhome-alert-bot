#!/bin/bash
set -euo pipefail

PROJECT_DIR="/Users/osori/workbench/applyhome-alert-bot"
LOG_DIR="$PROJECT_DIR/logs"
ENV_FILE="$PROJECT_DIR/.env"

mkdir -p "$LOG_DIR"
cd "$PROJECT_DIR"

if [ ! -f "$ENV_FILE" ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Missing .env file at $ENV_FILE" >> "$LOG_DIR/cron.log"
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

{
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting applyhome alert run"
  /Users/osori/.local/bin/uv run python -m applyhome_alert.main
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Finished applyhome alert run"
} >> "$LOG_DIR/cron.log" 2>&1
