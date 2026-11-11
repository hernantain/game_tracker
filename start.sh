#!/bin/bash
ROOT="$(cd "$(dirname "$0")" && pwd)"
APP_MODULE="backend.main:app"

# Production container: frontend is prebuilt into backend/static, so a single
# uvicorn process serves both the API and the static site.
if [ -d "$ROOT/backend/static" ]; then
    echo "Starting Racing Club Stats (production)..."
    exec uvicorn "$APP_MODULE" --host 0.0.0.0 --port "${PORT:-8080}"
fi

export PATH="/opt/homebrew/Cellar/node/23.3.0/bin:$PATH"
VENV="$ROOT/.venv/bin"

echo "Starting Racing Club Stats..."

# Start FastAPI backend
"$VENV/uvicorn" "$APP_MODULE" --host 0.0.0.0 --port 3001 --reload &
BACKEND_PID=$!
echo "Backend started (PID $BACKEND_PID) → http://localhost:3001"
echo "API docs available at: http://localhost:3001/docs"

# Start React frontend
cd "$ROOT/frontend" && npm run dev &
FRONTEND_PID=$!
echo "Frontend started (PID $FRONTEND_PID) → http://localhost:5173"

echo ""
echo "Dashboard ready at: http://localhost:5173"
echo "Press Ctrl+C to stop both servers."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
