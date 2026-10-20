


import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _commun import PLAFOND_FILS, PLANCHER_FILS, cible_autorisee, fils_depuis_compteur

echecs = []


def etape(nom, condition):
    print(("OK  " if condition else "KO  ") + nom)
    if not condition:
        echecs.append(nom)



etape("compteur a 0 -> plancher", fils_depuis_compteur(0) == PLANCHER_FILS)
etape("compteur enorme -> plafond (ne casse pas la demo)", fils_depuis_compteur(100000) == PLAFOND_FILS)
etape("compteur negatif -> plancher", fils_depuis_compteur(-20) == PLANCHER_FILS)
etape("entree invalide -> plancher", fils_depuis_compteur("abc") == PLANCHER_FILS)
etape("intensite croit avec le compteur", fils_depuis_compteur(5) < fils_depuis_compteur(30))
etape("toujours dans les bornes pour 0..5000",
      all(PLANCHER_FILS <= fils_depuis_compteur(n) <= PLAFOND_FILS for n in range(0, 5001, 7)))


etape("localhost autorise", cible_autorisee("127.0.0.1") and cible_autorisee("localhost"))
etape("reseau du groupe autorise", cible_autorisee("192.168.137.50"))
etape("adresse publique refusee", not cible_autorisee("8.8.8.8"))
etape("autre reseau prive refuse", not cible_autorisee("10.0.0.1"))

print("\n%s : %d etape(s) en echec" % ("ECHEC" if echecs else "SUCCES", len(echecs)))
sys.exit(1 if echecs else 0)
