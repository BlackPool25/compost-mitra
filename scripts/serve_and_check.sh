#!/usr/bin/env bash
# Automated health check script for CompostMitra Streamlit shell
# Cold-starts Streamlit, polls /_stcore/health until "ok", verifies startup < 3s,
# and cleans up background processes cleanly.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_DIR}"

PORT=8501
HEALTH_URL="http://localhost:${PORT}/_stcore/health"
MAX_STARTUP_SECONDS=3.0
LOG_FILE="/tmp/streamlit_serve.log"

STREAMLIT_PID=""

cleanup() {
    local exit_code=$?
    if [ -n "${STREAMLIT_PID}" ]; then
        if kill -0 "${STREAMLIT_PID}" 2>/dev/null; then
            echo "[serve_and_check] Terminating Streamlit server (PID: ${STREAMLIT_PID})..."
            kill -TERM "${STREAMLIT_PID}" 2>/dev/null || true
            wait "${STREAMLIT_PID}" 2>/dev/null || true
        fi
    fi
    exit ${exit_code}
}

trap cleanup EXIT INT TERM

echo "[serve_and_check] Launching Streamlit on port ${PORT}..."
START_TIME=$(date +%s%N)

# Launch Streamlit in headless mode
.venv/bin/streamlit run app.py --server.headless true --server.port "${PORT}" > "${LOG_FILE}" 2>&1 &
STREAMLIT_PID=$!

echo "[serve_and_check] Streamlit process started with PID: ${STREAMLIT_PID}"
echo "[serve_and_check] Polling ${HEALTH_URL} for 'ok' response..."

HEALTHY=false
while true; do
    CURRENT_TIME=$(date +%s%N)
    ELAPSED=$(awk -v s="${START_TIME}" -v c="${CURRENT_TIME}" 'BEGIN { printf "%.3f", (c - s) / 1000000000 }')

    # Ensure process is still running
    if ! kill -0 "${STREAMLIT_PID}" 2>/dev/null; then
        echo "[serve_and_check] ERROR: Streamlit process died prematurely. Process output:"
        cat "${LOG_FILE}"
        exit 1
    fi

    # Poll health endpoint
    RESPONSE=$(curl -sf "${HEALTH_URL}" 2>/dev/null || true)
    if [ "${RESPONSE}" = "ok" ]; then
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
