#!/usr/bin/env bash


set -u
RACINE="$(cd "$(dirname "$0")/.." && pwd)"
SDK="${RENPY_SDK:-$HOME/.local/opt/renpy-8.5.3-sdk}"
PORT=8765
if curl -s -o /dev/null "http://127.0.0.1:$PORT/health"; then
  echo "Un service répond déjà sur le port $PORT : j'utilise celui-là."
else
  ( cd "$RACINE/services/simulateur" && exec setsid nohup uv run uvicorn main:app --port "$PORT" --log-level warning > /tmp/simulateur.log 2>&1 ) &
  for _ in $(seq 1 40); do curl -s -o /dev/null "http://127.0.0.1:$PORT/health" && break; sleep 1; done
fi
curl -s "http://127.0.0.1:$PORT/health" | head -c 200; echo
( exec setsid nohup "$SDK/renpy.sh" "$RACINE/renpy" > /tmp/jeu.log 2>&1 ) &
echo "Jeu lancé. Arrêt : scripts/arreter.sh"
