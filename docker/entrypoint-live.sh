#!/bin/sh
# Entrypoint for the "live" Docker variant.
# Fetches fresh SOLVE-IT data from data.solveit-df.org at startup,
# then sets up a daily cron job to refresh it while the server runs.
#
# NOTE: The initial data fetch takes ~20-40 seconds depending on network.
#       The MCP server only starts AFTER the fetch completes.
#       Configure your MCP client with a startup timeout of at least 90 seconds.

DATA_URL="${SOLVE_IT_DATA_URL:-https://data.solveit-df.org/solve-it.json}"
# SOLVE_IT_BASE_DIR is the root that fetch_solveit_data.py writes into.
# SOLVE_IT_DATA_PATH (=/app/solve-it-main/data) is what the MCP server reads;
# it lives inside BASE_DIR, so we only need BASE_DIR here.
DATA_DIR="${SOLVE_IT_BASE_DIR:-/app/solve-it-main}"
FETCH_SCRIPT="/app/scripts/fetch_solveit_data.py"
REFRESH_HOUR="${SOLVE_IT_REFRESH_HOUR:-3}"   # hour (0-23) for daily refresh, default 03:00 UTC
LOG_PREFIX="[solve-it-live]"

# All output goes to stderr so it never corrupts the MCP stdio protocol
log() {
    echo "$LOG_PREFIX $*" >&2
}

fetch_data() {
    log "Fetching SOLVE-IT data from $DATA_URL ..."
    python3 "$FETCH_SCRIPT" --output "$DATA_DIR" --url "$DATA_URL" >&2
}

# ── Initial fetch (with one retry) ───────────────────────────────────────────
if fetch_data; then
    log "Initial data fetch complete."
else
    log "First fetch attempt failed. Retrying in 10 seconds..."
    sleep 10
    if fetch_data; then
        log "Retry succeeded."
    else
        log "ERROR: Failed to fetch SOLVE-IT data after 2 attempts. Cannot start server."
        exit 1
    fi
fi

# ── Daily refresh via crond ──────────────────────────────────────────────────
CRON_FILE="/etc/crontabs/mcpuser"
CRON_CMD="python3 $FETCH_SCRIPT --output $DATA_DIR --url $DATA_URL >/proc/1/fd/2 2>&1"

if [ -w "$(dirname "$CRON_FILE")" ] || [ -w "$CRON_FILE" ]; then
    echo "0 ${REFRESH_HOUR} * * * $CRON_CMD" > "$CRON_FILE"
    chmod 600 "$CRON_FILE"
    crond -l 8 2>/dev/null \
        && log "Daily refresh scheduled at ${REFRESH_HOUR}:00 UTC." \
        || log "Warning: crond not available — daily refresh disabled. Restart container to refresh."
else
    log "Warning: cannot write crontab (read-only fs?) — daily refresh disabled."
fi

# ── Start MCP server ─────────────────────────────────────────────────────────
log "Starting MCP server (transport=${MCP_TRANSPORT:-http}) ..."
exec python3 /app/src/server.py --transport "${MCP_TRANSPORT:-http}"
