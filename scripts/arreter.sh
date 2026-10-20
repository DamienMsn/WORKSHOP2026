#!/usr/bin/env bash

RACINE="$(cd "$(dirname "$0")/.." && pwd)"

MOTIF="$(printf '%s' "$RACINE" | sed 's/[][()\.^$*+?{}|]/\\&/g')"
pkill -9 -u "$USER" -f "[p]y3-linux-x86_64/renpy $MOTIF/renpy" 2>/dev/null
pkill -9 -u "$USER" -f "[r]enpy renpy test" 2>/dev/null
pkill -9 -u "$USER" -f "[u]vicorn main:app --port 8765" 2>/dev/null

pkill -9 -u "$USER" -f "[u]vicorn main:app --port 8770" 2>/dev/null
pkill -9 -u "$USER" -f "[u]vicorn main:app --port 8772" 2>/dev/null
echo "Jeu, simulateur et services reels arrêtés."
