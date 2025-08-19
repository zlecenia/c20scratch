#!/usr/bin/env bash
# Script to stop Python services running on configured port
# Reads PORT from .env file, falls back to env.example, defaults to 5005

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

log() { printf "\033[1;32m[stop]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }
err() { printf "\033[1;31m[error]\033[0m %s\n" "$*" 1>&2; }

# Function to read PORT from config files
get_port() {
    local port=""
    
    # Try to read from .env first
    if [[ -f "$ROOT_DIR/.env" ]]; then
        port=$(grep "^PORT=" "$ROOT_DIR/.env" 2>/dev/null | cut -d= -f2 | tr -d ' "'"'" || true)
        if [[ -n "$port" ]]; then
            echo "$port"
            return
        fi
    fi
    
    # Fall back to env.example
    if [[ -f "$ROOT_DIR/env.example" ]]; then
        port=$(grep "^PORT=" "$ROOT_DIR/env.example" 2>/dev/null | cut -d= -f2 | tr -d ' "'"'" || true)
        if [[ -n "$port" ]]; then
            echo "$port"
            return
        fi
    fi
    
    # Default port
    echo "5005"
}

# Get the port to stop services on
PORT=$(get_port)
log "Looking for Python services on port $PORT"

# Find processes using the port
PIDS=$(lsof -ti :$PORT 2>/dev/null || true)

if [[ -z "$PIDS" ]]; then
    log "No services found running on port $PORT"
    exit 0
fi

log "Found processes on port $PORT: $PIDS"

# Check if any of them are Python processes
PYTHON_PIDS=""
for pid in $PIDS; do
    # Check if it's a Python process
    PROCESS_INFO=$(ps -p $pid -o comm= 2>/dev/null || true)
    if [[ "$PROCESS_INFO" == *"python"* ]]; then
        PYTHON_PIDS="$PYTHON_PIDS $pid"
    fi
done

if [[ -z "$PYTHON_PIDS" ]]; then
    warn "Found processes on port $PORT but none are Python processes"
    log "All processes on port $PORT:"
    lsof -i :$PORT 2>/dev/null || true
    exit 0
fi

log "Found Python processes to stop:$PYTHON_PIDS"

# Stop Python processes gracefully first (SIGTERM)
for pid in $PYTHON_PIDS; do
    if kill -0 $pid 2>/dev/null; then
        log "Sending SIGTERM to Python process $pid"
        kill -TERM $pid 2>/dev/null || true
    fi
done

# Wait a moment for graceful shutdown
sleep 2

# Check if any are still running and force kill if needed
REMAINING_PIDS=""
for pid in $PYTHON_PIDS; do
    if kill -0 $pid 2>/dev/null; then
        REMAINING_PIDS="$REMAINING_PIDS $pid"
    fi
done

if [[ -n "$REMAINING_PIDS" ]]; then
    warn "Some processes didn't stop gracefully, force killing:$REMAINING_PIDS"
    for pid in $REMAINING_PIDS; do
        log "Sending SIGKILL to Python process $pid"
        kill -KILL $pid 2>/dev/null || true
    done
fi

# Final check
sleep 1
FINAL_CHECK=$(lsof -ti :$PORT 2>/dev/null || true)
if [[ -z "$FINAL_CHECK" ]]; then
    log "Successfully stopped all services on port $PORT"
else
    err "Some processes are still running on port $PORT:"
    lsof -i :$PORT 2>/dev/null || true
    exit 1
fi
