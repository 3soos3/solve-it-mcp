#!/bin/sh
# Entrypoint for the :live image.
# Checks if SOLVE_IT_DATA_URL is reachable; downloads fresh data if so.
# Falls back to cached data on any failure or if the source is unavailable.

set -e

DATA_DIR="${SOLVE_IT_DATA_PATH:-/tmp/app-cache/solve-it/data}"
DATA_PARENT="$(dirname "$DATA_DIR")"
ARCHIVE_PATH="/tmp/app-tmp/solve-it-latest.zip"
DATA_URL="${SOLVE_IT_DATA_URL:-https://data.solveit-df.org/solve-it-latest.zip}"

mkdir -p "$DATA_PARENT" /tmp/app-tmp

echo "[entrypoint] Checking ${DATA_URL} ..."

if wget --spider --quiet --timeout=10 --tries=1 "$DATA_URL" 2>/dev/null; then
    echo "[entrypoint] Reachable — fetching latest data ..."
    if wget --no-verbose --timeout=60 -O "$ARCHIVE_PATH" "$DATA_URL"; then
        echo "[entrypoint] Extracting to ${DATA_PARENT} ..."
        unzip -q -o "$ARCHIVE_PATH" -d "$DATA_PARENT"
        rm -f "$ARCHIVE_PATH"
        echo "[entrypoint] Data ready at ${DATA_DIR}"
    else
        rm -f "$ARCHIVE_PATH"
        echo "[entrypoint] Download failed — using cached data." >&2
    fi
else
    echo "[entrypoint] Unreachable — using cached data." >&2
fi

exec python3 /app/src/server.py "$@"
