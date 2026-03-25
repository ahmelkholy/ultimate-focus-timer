#!/bin/bash
# Focus Timer Daemon Launcher (bash/sh/linux/mac)
# Usage: bash focus-daemon.sh [start|stop|status]

DAEMON_URL="http://127.0.0.1:8765"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DAEMON_PID_FILE="$PROJECT_DIR/daemon.pid"

case "${1:-start}" in
    start)
        echo "[+] Starting Focus Timer daemon..."
        if [ -f "$DAEMON_PID_FILE" ]; then
            OLD_PID=$(cat "$DAEMON_PID_FILE")
            if kill -0 "$OLD_PID" 2>/dev/null; then
                echo "[!] Daemon already running (PID: $OLD_PID)"
                exit 1
            fi
        fi

        cd "$PROJECT_DIR"
        .venv/Scripts/python.exe -m src.daemon > "$PROJECT_DIR/daemon.log" 2>&1 &
        echo $! > "$DAEMON_PID_FILE"
        sleep 2

        # Verify it started
        if curl -s "$DAEMON_URL/status" > /dev/null; then
            echo "[OK] Daemon started on $DAEMON_URL (PID: $(cat $DAEMON_PID_FILE))"
        else
            echo "[X] Daemon failed to start"
            rm -f "$DAEMON_PID_FILE"
            exit 1
        fi
        ;;

    stop)
        echo "[+] Stopping Focus Timer daemon..."
        if [ ! -f "$DAEMON_PID_FILE" ]; then
            echo "[!] Daemon not running"
            exit 1
        fi
        PID=$(cat "$DAEMON_PID_FILE")
        kill $PID
        rm -f "$DAEMON_PID_FILE"
        echo "[OK] Daemon stopped"
        ;;

    status)
        if [ ! -f "$DAEMON_PID_FILE" ]; then
            echo "[!] Daemon not running"
            exit 1
        fi
        PID=$(cat "$DAEMON_PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            RESPONSE=$(curl -s "$DAEMON_URL/status")
            PHASE=$(echo "$RESPONSE" | grep -o '"phase":"[^"]*"' | cut -d'"' -f4)
            echo "[OK] Daemon running (PID: $PID, Phase: $PHASE)"
        else
            echo "[!] Daemon process not found (stale PID file)"
            rm -f "$DAEMON_PID_FILE"
            exit 1
        fi
        ;;

    *)
        echo "Usage: $0 {start|stop|status}"
        exit 1
        ;;
esac
