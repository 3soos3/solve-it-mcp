#!/bin/sh
# Entrypoint for the "live" Docker variant.
# Fetches fresh SOLVE-IT data from data.solveit-df.org at startup,
# then sets up a daily cron job to refresh it while the server runs.

set -e

DATA_URL="${SOLVE_IT_DATA_URL:-https://data.solveit-df.org/solve-it.json}"
# SOLVE_IT_BASE_DIR is the root that fetch_solveit_data.py writes into.
# SOLVE_IT_DATA_PATH (=/app/solve-it-main/data) is what the MCP server reads;
# it lives inside BASE_DIR, so we only need BASE_DIR here.
DATA_DIR="${SOLVE_IT_BASE_DIR:-/app/solve-it-main}"
FETCH_SCRIPT="/app/scripts/fetch_solveit_data.py"
REFRESH_HOUR="${SOLVE_IT_REFRESH_HOUR:-3}"   # hour (0-23) for daily refresh, default 03:00 UTC
LOG_PREFIX="[solve-it-live]"

log() {
    echo "$LOG_PREFIX $*"
}

fetch_data() {
    log "Fetching SOLVE-IT data from $DATA_URL ..."
    python3 "$FETCH_SCRIPT" --output "$DATA_DIR" --url "$DATA_URL"
    log "Data fetch complete."
}

# ── Initial fetch ────────────────────────────────────────────────────────────
fetch_data

# ── Daily refresh via crond ──────────────────────────────────────────────────
# Alpine crond requires the crontab to be written to /etc/crontabs/<user>.
# We run crond in the background and write the cron entry for mcpuser.

CRON_FILE="/etc/crontabs/mcpuser"
CRON_CMD="python3 $FETCH_SCRIPT --output $DATA_DIR --url $DATA_URL >> /proc/1/fd/1 2>&1"

# Write crontab (only if we can — might not have write permission in rootless mode)
if [ -w "$(dirname "$CRON_FILE")" ] || [ -w "$CRON_FILE" ]; then
    echo "0 ${REFRESH_HOUR} * * * $CRON_CMD" > "$CRON_FILE"
    chmod 600 "$CRON_FILE"
    # Start crond in background (-f = foreground would block, -l 8 = loglevel notice)
    crond -l 8 2>/dev/null && log "Daily refresh scheduled at ${REFRESH_HOUR}:00 UTC." || \
        log "Warning: crond not available — daily refresh disabled. Restart container to refresh."
else
    log "Warning: cannot write crontab (read-only fs?) — daily refresh disabled."
fi

# ── Start MCP server ─────────────────────────────────────────────────────────
log "Starting MCP server (transport=${MCP_TRANSPORT:-http}) ..."
exec python3 /app/src/server.py --transport "${MCP_TRANSPORT:-http}"
