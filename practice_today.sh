#!/bin/bash
# Blackwell Interview Flight Simulator — Practice Today
# Usage: ./practice_today.sh [mode]
# Modes: technical_deep_dive (default), behavioral_star, system_design, etc.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

MODE="${1:-technical_deep_dive}"

echo "🎯 Interview Flight Simulator"
echo "Mode: $MODE"
echo ""

# Setup venv
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    echo "✅ Environment ready"
else
    source venv/bin/activate
fi

# Kill any previous server
fuser -k 8081/tcp 2>/dev/null || true
sleep 1

# Start server
echo "🚀 Starting server on port 8081..."
uvicorn app.main:app --host 127.0.0.1 --port 8081 --app-dir . &
SERVER_PID=$!

# Wait for server to be ready
echo "⏳ Waiting for server..."
for i in $(seq 1 10); do
    if curl -sf http://127.0.0.1:8081/api/health >/dev/null 2>&1; then
        echo "✅ Server ready"
        break
    fi
    sleep 0.5
done

# Open browser
if [ -x /usr/bin/xdg-open ]; then
    echo "🌐 Opening browser..."
    xdg-open "http://127.0.0.1:8081/"
fi

echo ""
echo "📋 Voice Features:"
echo "   • Questions are read aloud automatically"
echo "   • Press 'Start Speaking' to answer with your voice"
echo "   • Press 'Stop Speaking' when done"
echo "   • Press 'Speak Question Again' to hear the question again"
echo "   • Type your answer if voice is unavailable"
echo ""
echo "🎤 Voice requirements:"
echo "   • Chrome or Edge browser (Firefox has limited Web Speech support)"
echo "   • Allow microphone access when prompted"
echo ""
echo "⚡ Quick test command:"
echo "   curl -s http://127.0.0.1:8081/"
echo ""
echo "Press Ctrl+C to stop the server."
echo ""

# Handle cleanup
cleanup() {
    echo "Stopping server..."
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
    echo "Bye!"
}
trap cleanup EXIT INT TERM

# Wait for user to press Ctrl+C
wait $SERVER_PID
