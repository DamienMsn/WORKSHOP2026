




import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8770"
echecs = []


def appel(methode, chemin, corps=None, jeton=None):
    donnees = json.dumps(corps).encode() if corps is not None else None
    req = urllib.request.Request(BASE + chemin, data=donnees, method=methode,
                                 headers={"Content-Type": "application/json"})
    if jeton:
        req.add_header("Authorization", "Bearer " + jeton)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
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


TX = dict(amount_cents=1250, currency="EUR", payer="caissier", payee="boutique-fictive")


code, corps = appel("GET", "/health")
etape("sante honnete ok, mode reel", code == 200 and corps["status"] == "ok"
      and corps["last_transaction_ok"] is True and corps["mode"] == "reel")


code, corps = appel("POST", "/auth/token", dict(username="demo", password="demo"))
etape("jeton obtenu, mode reel annonce", code == 200 and corps["mode"] == "reel" and corps.get("access_token"))
jeton = corps.get("access_token")
code, _ = appel("POST", "/auth/token", dict(username="demo", password="faux"))
etape("mauvais mot de passe refuse (401)", code == 401)


code, _ = appel("POST", "/transactions", TX)
etape("transaction sans jeton refusee (401)", code == 401)
code, corps = appel("POST", "/transactions", TX, jeton)
etape("transaction acceptee (201), statut accepted, mode reel",
      code == 201 and corps["status"] == "accepted" and corps["mode"] == "reel" and corps.get("id"))
tx_id = corps.get("id")
code, corps = appel("GET", "/transactions/%s" % tx_id, jeton=jeton)
etape("transaction relue par id (persistance reelle)", code == 200 and corps["id"] == tx_id)
code, _ = appel("GET", "/transactions/%s" % tx_id)
etape("relecture sans jeton refusee (401)", code == 401)
code, _ = appel("GET", "/transactions/inconnue-xyz", jeton=jeton)
etape("transaction inconnue : 404", code == 404)


cle = "smoke-" + tx_id
code1, c1 = appel("POST", "/transactions", dict(TX, idempotency_key=cle), jeton)
code2, c2 = appel("POST", "/transactions", dict(TX, idempotency_key=cle), jeton)
etape("idempotence : meme cle rejoue la meme transaction", c1.get("id") == c2.get("id") and c1.get("id"))


m = brut("/metrics")
etape("metriques exposees, compteur de transactions ok present",
      'alpha_transactions_total{issue="ok"}' in m and "alpha_requests_total" in m)

print("\n%s : %d etape(s) en echec" % ("ECHEC" if echecs else "SUCCES", len(echecs)))
sys.exit(1 if echecs else 0)
