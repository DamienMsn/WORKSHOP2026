#!/usr/bin/env bash





set -u
unset SIM_LLM NANOGPT_API_KEY   # les tests n'appellent jamais de modèle externe
RACINE="$(cd "$(dirname "$0")/.." && pwd)"
SDK="${RENPY_SDK:-$HOME/.local/opt/renpy-8.5.3-sdk}"
PORT=${ALPHA_PORT_TEST:-8799}   # autre port que la démonstration (8765)
PIDS=()
DEBUT=$(date +%s)
fermer() {
  for p in "${PIDS[@]}"; do kill -9 -- "-$p" 2>/dev/null; kill -9 "$p" 2>/dev/null; done
  pkill -9 -u "$USER" -f "[r]enpy renpy test" 2>/dev/null
  pkill -9 -u "$USER" -f "[u]vicorn main:app --port $PORT" 2>/dev/null
}
trap fermer EXIT
sed "s/8765/$PORT/g" "$RACINE/config/interfaces.json" > /tmp/alpha-test-config.json
export ALPHA_CONFIG=/tmp/alpha-test-config.json ATTAQUE_DUREE_S=3
( cd "$RACINE/services/simulateur" && DELAI_DETECTION_S=1.5 DELAI_REPRISE_S=2.5 exec setsid uv run uvicorn main:app --port "$PORT" --log-level warning ) &
PIDS+=($!)
for _ in $(seq 1 40); do curl -s -o /dev/null "http://127.0.0.1:$PORT/health" && break; sleep 1; done
setsid timeout -k 2 170 "$SDK/renpy.sh" "$RACINE/renpy" test "${1:-jeu}" --hide-header ${1:+--overwrite-screenshots} > /tmp/test-jeu.log 2>&1 &
PIDS+=($!)
wait "${PIDS[1]}"
python3 -I - "$DEBUT" <<'PYEOF'
import re, sys, time
log = open("/tmp/test-jeu.log", encoding="utf-8", errors="replace").read()
duree = int(time.time()) - int(sys.argv[1])
cas = re.search(r"Test cases :\s+(\d+) \|\s+(\d+) passed .*?\|\s+(\d+) failed", log)
ver = re.search(r"Assertions :\s+(\d+) \|\s+(\d+) passed .*?\|\s+(\d+) failed", log)
if not cas:
    print("KO : le test n'a pas pu démarrer (voir /tmp/test-jeu.log)")
    print("\n".join(l for l in log.splitlines() if re.search(r"rror|Exception", l))[:600])
    sys.exit(1)
total, ok, ko = map(int, cas.groups())
print("%s : %d/%d parcours exécutés, %s vérifications en %d s" % ("OK" if ko == 0 else "KO", ok, ok + ko, ver.group(2) if ver else "?", duree))
if ko:
    for bloc in re.findall(r"\[exc\]     - (\w+)\n(.*?)(?=\[rpytest\])", log, flags=re.S):
        m = re.search(r"(AssertionError|AttributeError|NameError|\w*Error): (.*)", bloc[1])
        if m:
            print("  - %s : %s" % (bloc[0], m.group(0)[:140]))
sys.exit(1 if ko else 0)
PYEOF
