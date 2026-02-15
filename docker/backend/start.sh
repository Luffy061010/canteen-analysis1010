#!/bin/sh
set -e

java -jar /app/backend/canteen-analysis.jar &
JAVA_PID=$!

python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir /app/python &
PY_PID=$!

trap 'kill -TERM "$JAVA_PID" "$PY_PID" 2>/dev/null || true' INT TERM

while true; do
  if ! kill -0 "$JAVA_PID" 2>/dev/null; then
    wait "$JAVA_PID"
    exit $?
  fi

  if ! kill -0 "$PY_PID" 2>/dev/null; then
    wait "$PY_PID"
    exit $?
  fi

  sleep 2
done
