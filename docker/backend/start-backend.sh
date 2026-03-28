#!/bin/sh
set -eu

cd /app/python
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
PY_PID=$!

cd /app
java -jar /app/java/canteen-analysis.jar &
JAVA_PID=$!

terminate_all() {
  kill -TERM "$PY_PID" "$JAVA_PID" 2>/dev/null || true
  wait "$PY_PID" 2>/dev/null || true
  wait "$JAVA_PID" 2>/dev/null || true
}

trap terminate_all INT TERM

while true; do
  if ! kill -0 "$PY_PID" 2>/dev/null; then
    wait "$PY_PID" || true
    terminate_all
    exit 1
  fi

  if ! kill -0 "$JAVA_PID" 2>/dev/null; then
    wait "$JAVA_PID" || true
    terminate_all
    exit 1
  fi

  sleep 1
done
