#!/usr/bin/env bash
set -euo pipefail

# run_local.sh - Set up and start backend and frontend locally
# Usage: ./run_local.sh

ROOT_DIR=$(cd "$(dirname "$0")" && pwd)
VENV_DIR="$ROOT_DIR/.venv"

echo "=== Setting up Python virtualenv (if missing) ==="
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel

echo "=== Installing backend Python dependencies ==="
pip install -r "$ROOT_DIR/FlacLossless-main/backend/requirements.txt"

echo "=== Installing frontend Node dependencies ==="
cd "$ROOT_DIR/FlacLossless-main"
if [ ! -d node_modules ]; then
  npm install --no-audit --no-fund --silent
fi

echo "=== Starting backend (Flask) ==="
cd "$ROOT_DIR"
# Backend log
BACKEND_LOG="$ROOT_DIR/backend.log"
# Start backend in background
source "$VENV_DIR/bin/activate"
nohup python3 "$ROOT_DIR/FlacLossless-main/backend/server.py" > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID), logs: $BACKEND_LOG"

echo "=== Starting frontend dev server (Vite) ==="
cd "$ROOT_DIR/FlacLossless-main"
FRONTEND_LOG="$ROOT_DIR/fl_frontend.log"
nohup npm run dev > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!
echo "Frontend dev server started (PID: $FRONTEND_PID), logs: $FRONTEND_LOG"

echo
echo "Local servers started.
 - Frontend: http://127.0.0.1:5173
 - Backend:  http://127.0.0.1:3001

To stop: kill $BACKEND_PID $FRONTEND_PID
Check logs: tail -f $BACKEND_LOG $FRONTEND_LOG"
