#!/usr/bin/env bash
# Automated health check script for CompostMitra 2.0 FastAPI + React PWA server
# Cold-starts server, polls /api/health until healthy, verifies startup < 3s,
# and cleans up background processes cleanly.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_DIR}"

PORT=3000
HEALTH_URL="http://localhost:${PORT}/api/health"
MAX_STARTUP_SECONDS=3.0
LOG_FILE="/tmp/compostmitra_serve.log"

SERVER_PID=""

cleanup() {
    local exit_code=$?
    if [ -n "${SERVER_PID}" ]; then
        if kill -0 "${SERVER_PID}" 2>/dev/null; then
            echo "[serve_and_check] Terminating CompostMitra server (PID: ${SERVER_PID})..."
            kill -TERM "${SERVER_PID}" 2>/dev/null || true
            wait "${SERVER_PID}" 2>/dev/null || true
        fi
    fi
    exit ${exit_code}
}

trap cleanup EXIT INT TERM

echo "[serve_and_check] Launching CompostMitra 2.0 on port ${PORT}..."
START_TIME=$(date +%s%N)

# Launch FastAPI server in background
PORT="${PORT}" .venv/bin/python server.py > "${LOG_FILE}" 2>&1 &
SERVER_PID=$!

echo "[serve_and_check] Server process started with PID: ${SERVER_PID}"
echo "[serve_and_check] Polling ${HEALTH_URL} for healthy response..."

HEALTHY=false
while true; do
    CURRENT_TIME=$(date +%s%N)
    ELAPSED=$(awk -v s="${START_TIME}" -v c="${CURRENT_TIME}" 'BEGIN { printf "%.3f", (c - s) / 1000000000 }')

    # Ensure process is still running
    if ! kill -0 "${SERVER_PID}" 2>/dev/null; then
        echo "[serve_and_check] ERROR: Server process died prematurely. Process output:"
        cat "${LOG_FILE}"
        exit 1
    fi

    # Poll health endpoint
    RESPONSE=$(curl -sf "${HEALTH_URL}" 2>/dev/null || true)
    if echo "${RESPONSE}" | grep -q "healthy"; then
        HEALTHY=true
        echo "[serve_and_check] Health check passed: received '${RESPONSE}' in ${ELAPSED}s"
        break
    fi

    # Check timeout condition
    IS_TIMEOUT=$(awk -v e="${ELAPSED}" -v m="${MAX_STARTUP_SECONDS}" 'BEGIN { print (e > m) ? 1 : 0 }')
    if [ "${IS_TIMEOUT}" -eq 1 ]; then
        echo "[serve_and_check] ERROR: Cold startup exceeded limit (${ELAPSED}s > ${MAX_STARTUP_SECONDS}s)."
        cat "${LOG_FILE}"
        exit 1
    fi

    sleep 0.05
done

if [ "${HEALTHY}" = true ]; then
    echo "[serve_and_check] SUCCESS: Cold startup under 3.0s verified (${ELAPSED}s < 3.0s). Exiting 0."
    exit 0
else
    echo "[serve_and_check] ERROR: Health check failed."
    exit 1
fi
