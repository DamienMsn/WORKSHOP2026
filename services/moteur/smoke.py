






import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8773"
echecs = []


def appel(methode, chemin, corps=None):
    donnees = json.dumps(corps).encode() if corps is not None else None
    req = urllib.request.Request(BASE + chemin, data=donnees, method=methode,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)


def brut(chemin):
    with urllib.request.urlopen(BASE + chemin, timeout=10) as r:
        return r.read().decode()


def etape(nom, condition):
    print(("OK  " if condition else "KO  ") + nom)
    if not condition:
        echecs.append(nom)



code, corps = appel("GET", "/health")
etape("moteur en sante, mode reel", code == 200 and corps["status"] == "ok" and corps["mode"] == "reel")


alerte = dict(source="detecteur", kind="injection", severity="high", target="alpha-paiement",
              detail="pic d'injection SQL",
              recommendation=dict(summary="injection detectee", suggested_action="block_source",
                                  confidence=0.9, rationale="motif connu"))
code, corps = appel("POST", "/alerts", alerte)
etape("alerte acceptee (202), action dans la liste blanche",
      code == 202 and corps["action"] in ("block_source", "restart_service"))
etape("action executee avec succes (block_source, pas de docker requis)",
      corps["action"] == "block_source" and corps["action_ok"] is True)
etape("EX-08 : reprise OK, mesuree par de vraies verifications",
      corps["reprise_ok"] is True and all(v["status"] == "ok" for v in corps["verifications"]))
etape("les trois verifications sont presentes (api, transaction, donnees)",
      [v["name"] for v in corps["verifications"]] == ["api_accessible", "transaction_test", "donnees_coherentes"])


hors = dict(source="detecteur", kind="dos", severity="high", target="conteneur-interdit")
code, corps = appel("POST", "/alerts", hors)
etape("cible hors liste blanche : action refusee (garde-fou)",
      code == 202 and corps["action_ok"] is False and "hors liste blanche" in corps["action_detail"])


code, corps = appel("GET", "/verifications")
etape("dernieres verifications relisibles et toutes ok",
      code == 200 and all(v["status"] == "ok" for v in corps["verifications"]))
types = [e["type"] for e in appel("GET", "/events")[1]["events"]]
etape("journal : alerte, action, fin de remediation presents",
      "alert_received" in types and "action" in types and "remediation_done" in types)


m = brut("/metrics")
etape("metriques exposees, au moins une reprise ok comptee",
      'alpha_moteur_reprises_total{issue="ok"}' in m and "alpha_moteur_alertes_total" in m)

print("\n%s : %d etape(s) en echec" % ("ECHEC" if echecs else "SUCCES", len(echecs)))
sys.exit(1 if echecs else 0)
