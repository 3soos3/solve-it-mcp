#!/bin/sh
# Entrypoint for the :live image.
# Fetches SOLVE-IT data from SOLVE_IT_DATA_URL at startup, then starts the MCP server.

set -e

DATA_DIR="${SOLVE_IT_DATA_PATH:-/tmp/app-cache/solve-it/data}"
DATA_PARENT="$(dirname "$DATA_DIR")"
ARCHIVE_PATH="/tmp/app-tmp/solve-it-latest.zip"
DATA_URL="${SOLVE_IT_DATA_URL:-https://data.solveit-df.org/solve-it-latest.zip}"

echo "[entrypoint] Fetching SOLVE-IT data from ${DATA_URL} ..."
mkdir -p "$DATA_PARENT" /tmp/app-tmp

if wget --no-verbose -O "$ARCHIVE_PATH" "$DATA_URL"; then
    echo "[entrypoint] Extracting SOLVE-IT data ..."
    mkdir -p "$DATA_PARENT"
    unzip -q -o "$ARCHIVE_PATH" -d "$DATA_PARENT"
    rm -f "$ARCHIVE_PATH"
    echo "[entrypoint] SOLVE-IT data ready at ${DATA_DIR}"
else
    echo "[entrypoint] WARNING: Failed to fetch live data from ${DATA_URL}" >&2
    if [ -d "$DATA_DIR" ]; then
        echo "[entrypoint] Using cached data from previous run." >&2
    else
        echo "[entrypoint] No cached data available — server may fail to start." >&2
    fi
fi

exec python3 /app/src/server.py "$@"
