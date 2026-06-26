#!/bin/bash
# Quick launcher — auto-loads the 16-lane station JD into the simulator
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Setup venv
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
else
    source venv/bin/activate
fi

# Kill old server
fuser -k 8081/tcp 2>/dev/null || true
sleep 1

# Start server
uvicorn app.main:app --host 127.0.0.1 --port 8081 --app-dir . &
SERVER_PID=$!

# Wait for server
for i in $(seq 1 10); do
    if curl -sf http://127.0.0.1:8081/api/health >/dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

# Read the JD file
JD=$(cat study/16_lane_station_jd.md)

# Start a session with the JD pre-loaded
SESSION_ID=$(curl -s -X POST http://127.0.0.1:8081/api/start \
  -H "Content-Type: application/json" \
  -d "{\"job_description\": $(echo "$JD" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))'), \"role_title\": \"Python Automation Engineer\", \"mode\": \"technical_deep_dive\"}" | python3 -c 'import sys,json; print(json.loads(sys.stdin.read())["session_id"])')

echo "Session started: $SESSION_ID"
echo "Open: http://127.0.0.1:8081/"

# Open browser
xdg-open "http://127.0.0.1:8081/"

# Handle cleanup
cleanup() {
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
}
trap cleanup EXIT INT TERM
wait $SERVER_PID
