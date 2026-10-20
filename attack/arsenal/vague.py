










import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from _commun import PLANCHER_FILS, fils_depuis_compteur, lancer

COMPTEUR = os.environ.get("ALPHA_VAGUE_COMPTEUR", "http://127.0.0.1:8765/participation/etat")
ATTENTE_MAX_S = float(os.environ.get("ALPHA_VAGUE_ATTENTE_MAX_S", "600"))


def lire_etat():

    try:
        with urllib.request.urlopen(COMPTEUR, timeout=5) as r:
            return json.loads(r.read().decode())
    except (urllib.error.URLError, OSError, ValueError):
        return None


def attendre_depart() -> dict | None:

    debut = time.time()
    dernier = None
    while time.time() - debut < ATTENTE_MAX_S:
        etat = lire_etat()
        if etat is None:
            return None
        dernier = etat
        if etat.get("phase") == "termine":
            return etat
        if etat.get("phase") == "repos":
            print("[VAGUE] compteur au repos : rien a lancer", flush=True)
            return etat
        print("[VAGUE] %d participant(s), depart dans %s s" % (etat.get("total", 0), etat.get("decompte")), flush=True)
        time.sleep(1.0)
    return dernier


def main() -> int:
    etat = attendre_depart()
    if etat is None:
        n_fils = PLANCHER_FILS
        print("[VAGUE] compteur injoignable : mode local, intensite plancher (%d fils)" % n_fils, flush=True)
    elif etat.get("phase") == "repos":
        return 0
    else:
        total = etat.get("total", 0)
        n_fils = fils_depuis_compteur(total)
        print("[VAGUE] depart : %d participant(s) -> %d fils (borne)" % (total, n_fils), flush=True)
    return lancer(1, "Vague pilotee par le public (charge reelle)", n_fils)


if __name__ == "__main__":
    sys.exit(main())
