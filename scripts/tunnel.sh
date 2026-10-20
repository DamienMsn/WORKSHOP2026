#!/usr/bin/env bash








set -u
PORT="${1:-8765}"
CIBLE="http://127.0.0.1:${PORT}/participation"
BIN_DIR="${HOME}/.local/bin"
CF="$(command -v cloudflared || true)"
[ -z "$CF" ] && [ -x "${BIN_DIR}/cloudflared" ] && CF="${BIN_DIR}/cloudflared"

telecharger_cloudflared() {
  mkdir -p "$BIN_DIR"
  local os arch url
  os="$(uname -s | tr '[:upper:]' '[:lower:]')"
  arch="$(uname -m)"
  case "$arch" in x86_64|amd64) arch=amd64 ;; aarch64|arm64) arch=arm64 ;; *) echo "arch non geree: $arch" >&2; return 1 ;; esac
  if [ "$os" = "linux" ]; then
    url="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${arch}"
  else
    echo "Sur ${os} (ex. PC Hote Windows), installer cloudflared a la main :" >&2
    echo "  https://github.com/cloudflare/cloudflared/releases/latest" >&2
    return 1
  fi
  echo "cloudflared absent : telechargement officiel (Apache-2.0) -> ${BIN_DIR}/cloudflared" >&2
  curl -fL --retry 3 -o "${BIN_DIR}/cloudflared" "$url" || return 1
  chmod +x "${BIN_DIR}/cloudflared"
  CF="${BIN_DIR}/cloudflared"
}

if [ -z "$CF" ]; then
  telecharger_cloudflared || { echo "Impossible d'obtenir cloudflared." >&2; exit 1; }
fi


if ! curl -s -o /dev/null --max-time 3 "http://127.0.0.1:${PORT}/participation/etat"; then
  echo "Le compteur ne repond pas sur ${PORT}. Lancer d'abord le simulateur (scripts/lancer.sh)." >&2
  exit 1
fi

echo "Ouverture du tunnel vers ${CIBLE} ..."
LOG="$(mktemp)"
"$CF" tunnel --no-autoupdate --url "$CIBLE" > "$LOG" 2>&1 &
PID=$!
trap 'kill "$PID" 2>/dev/null; rm -f "$LOG"' EXIT INT TERM


URL=""
for _ in $(seq 1 30); do
  URL="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG" | head -n1 || true)"
  [ -n "$URL" ] && break
  sleep 1
done

if [ -z "$URL" ]; then
  echo "URL du tunnel introuvable. Sortie de cloudflared :" >&2
  cat "$LOG" >&2
  exit 1
fi

echo
echo "  URL publique a scanner : ${URL}"
echo "  QR (via le simulateur) : http://127.0.0.1:${PORT}/participation/qr.png?cible=${URL}"
echo
echo "  Encoder cette URL dans le QR du cockpit, ou ouvrir le lien QR ci-dessus."
echo "  Ctrl-C pour fermer le tunnel."
wait "$PID"
