


label start:
    $ pont_demarrer()
    show screen hud
    if ETAT.cfg.get("demo") and (interfaces_simulees() or not role_verrouille()):
        call screen s_demo_refusee
        return
    jump titre

label titre:
    $ choix = renpy.call_screen("s_titre")
    if choix == "hacker":
        call screen s_terminal
    elif choix == "client":
        call screen s_paiement
    elif choix == "soc":
        $ suite = renpy.call_screen("s_soc")
        if suite == "epilogue":
            call screen s_epilogue
    elif choix == "salle":
        call screen s_salle
    elif choix == "scenario":
        jump scenario
    elif choix == "repetition":
        jump repetition
    jump titre




label repetition:
    $ _passes = int(ETAT.cfg.get("repetition_passes", 10))
    $ ETAT.repetition = dict(passes=0, ok=0, en_cours=True)
    $ _i = 0
    while _i < _passes:
        $ ETAT.chrono_debut = None
        $ ETAT.chrono_fin = None
        $ http("POST", ETAT.cfg["plateforme"]["url"], "/simulation/reset")
        $ lancer_niveau(1)
        call screen scenario_salle()
        $ lancer_paiement()
        $ _t = 0
        while not paiement_fini() and _t < 40:
            pause 0.3
            $ _t += 1
        $ ETAT.repetition["passes"] += 1
        if paiement_ok():
            $ ETAT.repetition["ok"] += 1
        $ _i += 1
    $ ETAT.repetition["en_cours"] = False
    call screen intertitre("RÉPÉTITION (EX-12)", "%d/%d passages réussis, sans aucune intervention humaine." % (ETAT.repetition["ok"], ETAT.repetition["passes"]))
    jump titre




label scenario:
    $ ETAT.tx_ok = 0
    $ ETAT.tx_ko = 0
    $ ETAT.chrono_debut = None
    $ ETAT.chrono_fin = None
    call screen intertitre("RÉSILIENCE ALPHA", "Regardez une banque encaisser une attaque et se relever toute seule.")


    $ lancer_paiement()
    $ _t = 0
    while not paiement_fini() and _t < 40:
        pause 0.3
        $ _t += 1
    call screen intertitre("AVANT", "Le client paie. Le service répond. Tout va bien.")


    $ reset_vague()
    $ armer_vague(5)
    call screen s_vague_auto(6.0)
    $ lancer_niveau(1)
    $ _nb = vague_total()
    call screen intertitre("VOUS ÊTES LE BOTNET", ("Vous l'avez frappée à %d mains. L'attaque cogne." % _nb) if _nb else "L'attaque cogne. Le service vacille.")


    call screen intertitre("NE TOUCHEZ À RIEN", "Le système a vu. Il répare seul. Personne n'intervient.")
    call screen scenario_salle()


    $ lancer_paiement()
    $ _t = 0
    while not paiement_fini() and _t < 50:
        pause 0.3
        $ _t += 1
    call screen intertitre("APRÈS", "Le client repaie. Le service est revenu. Zéro intervention humaine.")


    call screen s_epilogue
    jump titre
