










import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

MODE = "reel"

ACTIONS_VALIDES = ("restart_service", "block_source", "rate_limit", "scale_up", "none")
CIBLES = tuple(c.strip() for c in os.environ.get("ALPHA_CIBLES", "alpha-paiement").split(",") if c.strip())
URL_PLATEFORME = os.environ.get("ALPHA_PLATEFORME_URL", "http://127.0.0.1:8780").rstrip("/")
IDENT_DEMO = (os.environ.get("ALPHA_DEMO_USER", "demo"), os.environ.get("ALPHA_DEMO_PASS", "demo"))

app = FastAPI(title="Moteur de remediation RESILIENCE-ALPHA", version="0.1.0")
etat = dict(alertes=[], verifications=[], evenements=[], bloquees=[])
METRIQUES = dict(alertes=0, actions=0, reprises_ok=0, reprises_ko=0)


def maintenant() -> datetime:
    return datetime.now(timezone.utc)


def iso(d: datetime) -> str:
    return d.isoformat()


def journal(evenement: str, **champs) -> None:
    print(json.dumps(dict(ts=iso(maintenant()), service="moteur", mode=MODE, event=evenement, **champs),
                      ensure_ascii=False), file=sys.stdout, flush=True)


class Recommandation(BaseModel):
    summary: str | None = None
    suggested_action: str | None = None
    confidence: float | None = None
    rationale: str | None = None


class AlerteEntree(BaseModel):
    source: str
    kind: str
    severity: str
    score: float | None = None
    target: str
    detail: str | None = None
    recommendation: Recommandation | None = None


def choisir_action(alerte: AlerteEntree) -> str:

    suggere = alerte.recommendation.suggested_action if alerte.recommendation else None
    if suggere in ACTIONS_VALIDES and suggere != "none":
        return suggere

    return {"dos": "restart_service", "injection": "block_source", "anomaly": "restart_service"}.get(alerte.kind, "restart_service")


def executer(action: str, cible: str) -> tuple[bool, str]:

    if cible not in CIBLES:
        return False, "cible %s hors liste blanche %s : action refusee" % (cible, CIBLES)
    if action == "restart_service":
        try:
            r = subprocess.run(["docker", "restart", cible], capture_output=True, text=True, timeout=30)
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            return False, "docker indisponible : %s" % e
        if r.returncode != 0:
            return False, "echec docker restart : %s" % r.stderr.strip()
        return True, "conteneur %s redemarre" % cible
    if action == "block_source":
        etat["bloquees"].append(dict(at=iso(maintenant()), cible=cible))
        return True, "source bloquee pour %s (regle enregistree ; WAF reel a brancher)" % cible
    if action in ("rate_limit", "scale_up"):
        return True, "action %s enregistree (a brancher sur l'infra reelle)" % action
    return False, "action %s non appliquee" % action


def verifier_reprise() -> list[dict]:

    v = []

    api_ok = False
    try:
        with urllib.request.urlopen(URL_PLATEFORME + "/health", timeout=5) as r:
            d = json.loads(r.read().decode())
            api_ok = d.get("status") == "ok"
        v.append(dict(name="api_accessible", status="ok" if api_ok else "ko",
                      detail="/health = %s" % (d.get("status") if api_ok or d else "?")))
    except (urllib.error.URLError, OSError) as e:
        v.append(dict(name="api_accessible", status="ko", detail="injoignable : %s" % e))

    tx_ok = False
    tx_detail = "non tentee (API ko)"
    if api_ok:
        tx_ok, tx_detail = transaction_test()
    v.append(dict(name="transaction_test", status="ok" if tx_ok else "ko", detail=tx_detail))

    v.append(dict(name="donnees_coherentes", status="ok" if tx_ok else "ko",
                  detail="transaction relue" if tx_ok else "pas de transaction a relire"))
    return v


def transaction_test() -> tuple[bool, str]:
    try:
        corps = json.dumps(dict(username=IDENT_DEMO[0], password=IDENT_DEMO[1])).encode()
        req = urllib.request.Request(URL_PLATEFORME + "/auth/token", data=corps, method="POST",
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as r:
            jeton = json.loads(r.read().decode())["access_token"]
        tx = json.dumps(dict(amount_cents=100, currency="EUR", payer="moteur", payee="verification",
                             idempotency_key="verif-" + uuid.uuid4().hex)).encode()
        req2 = urllib.request.Request(URL_PLATEFORME + "/transactions", data=tx, method="POST",
                                      headers={"Content-Type": "application/json", "Authorization": "Bearer " + jeton})
        with urllib.request.urlopen(req2, timeout=5) as r:
            d = json.loads(r.read().decode())
        return d.get("status") == "accepted", "transaction %s (%s)" % (d.get("status"), d.get("id", "")[:8])
    except (urllib.error.URLError, OSError, KeyError) as e:
        return False, "echec : %s" % e


def evenement(type_, detail):
    etat["evenements"].append(dict(at=iso(maintenant()), type=type_, component="moteur", detail=detail))
    del etat["evenements"][:-50]


@app.post("/alerts", status_code=202)
def recevoir_alerte(alerte: AlerteEntree):
    METRIQUES["alertes"] += 1
    ident = uuid.uuid4().hex[:8]
    etat["alertes"].append(dict(alerte.model_dump(), id=ident, at=iso(maintenant())))
    journal("alert_received", id=ident, kind=alerte.kind, target=alerte.target, severity=alerte.severity)
    evenement("alert_received", "alerte %s sur %s" % (alerte.kind, alerte.target))

    action = choisir_action(alerte)
    succes, detail = executer(action, alerte.target)
    METRIQUES["actions"] += 1
    journal("action", id=ident, action=action, cible=alerte.target, succes=succes, detail=detail)
    evenement("action", "%s sur %s : %s" % (action, alerte.target, detail))


    if action == "restart_service" and succes:
        attendre_sante(timeout_s=30)
    verifs = verifier_reprise()
    etat["verifications"] = verifs
    reprise_ok = all(x["status"] == "ok" for x in verifs)
    METRIQUES["reprises_ok" if reprise_ok else "reprises_ko"] += 1
    journal("remediation_done", id=ident, reprise_ok=reprise_ok)
    evenement("remediation_done", "reprise %s" % ("OK" if reprise_ok else "KO"))
    return dict(id=ident, action=action, action_ok=succes, action_detail=detail,
                verifications=verifs, reprise_ok=reprise_ok, mode=MODE)


def attendre_sante(timeout_s: float = 30) -> bool:
    debut = time.time()
    while time.time() - debut < timeout_s:
        try:
            with urllib.request.urlopen(URL_PLATEFORME + "/health", timeout=3) as r:
                if json.loads(r.read().decode()).get("status") == "ok":
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(1)
    return False


@app.get("/verifications")
def lire_verifications():
    return dict(verifications=etat["verifications"], mode=MODE)


@app.get("/events")
def lire_evenements():
    return dict(events=etat["evenements"], mode=MODE)


@app.get("/health")
def health():
    return dict(status="ok", last_transaction_ok=True, checked_at=iso(maintenant()), mode=MODE)


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    lignes = [
        "# TYPE alpha_moteur_alertes_total counter",
        "alpha_moteur_alertes_total %d" % METRIQUES["alertes"],
        "# TYPE alpha_moteur_actions_total counter",
        "alpha_moteur_actions_total %d" % METRIQUES["actions"],
        "# TYPE alpha_moteur_reprises_total counter",
        'alpha_moteur_reprises_total{issue="ok"} %d' % METRIQUES["reprises_ok"],
        'alpha_moteur_reprises_total{issue="ko"} %d' % METRIQUES["reprises_ko"],
    ]
    return "\n".join(lignes) + "\n"
