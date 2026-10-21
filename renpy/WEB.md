# Portage web du cockpit (Ren'Py WebAssembly)

Le cockpit parle à des services HTTP et lançait des attaques via `subprocess`.
Le navigateur interdit sockets bruts et processus locaux. La couche réseau de
`game/pont.rpy` a donc été rendue **compatible web ET natif**, en branchant sur
`renpy.emscripten`.

## Ce qui est déjà intégré dans `game/pont.rpy`

| Élément | Natif | Web (`renpy.emscripten`) |
|---|---|---|
| `http_brut()` | urllib (inchangé) | `_http_brut_web()` → `renpy.fetch()` |
| `rafraichir_qr_vague()` | urllib + écriture `game/cache` | mémorise `ETAT.qr_vague_url` (FS en lecture seule) |
| Sondage santé | thread `boucle_sante()` | `config.periodic_callback = _tic_sonde_web` |
| `Job` (paiement, question) | thread | exécution inline (fetch bloque brièvement) |
| `declarer()` (events) | thread | inline |
| `lancer_niveau()` (attaques) | `subprocess` | message « indisponible en web » |

Le contrat de retour `dict(code, data, mode, erreur)` est identique.
`renpy.FetchError.status_code` fournit les codes HTTP (401/503…). Le `mode` est
lu dans le corps JSON (les services le renvoient déjà), l'en-tête `X-Mode`
n'étant plus accessible via `fetch`.

## Ce qu'il reste à faire pour un build web réellement jouable

1. **Exposer les services en HTTPS + CORS.** Le navigateur refuse
   `http://127.0.0.1:8765` et le cross-origin sans en-têtes. Ajouter à chaque
   service FastAPI :
   ```python
   from fastapi.middleware.cors import CORSMiddleware
   app.add_middleware(CORSMiddleware, allow_origins=["https://<domaine-du-jeu>"],
                      allow_methods=["*"], allow_headers=["*"])
   ```
   Puis pointer `config/interfaces.json` sur les URL publiques.

2. **Déporter les attaques côté serveur.** `subprocess` est impossible en web.
   Créer p.ex. `POST /attaque/lancer` et `POST /attaque/arreter` (sur le moteur
   ou la détection) qui exécutent les scripts `attack/…`, et réécrire
   `lancer_niveau()` / `arreter_script()` pour les appeler via `http()`.

3. **En-têtes COOP/COEP à l'hébergement** (requis par le `SharedArrayBuffer`
   de Ren'Py web) :
   ```
   Cross-Origin-Opener-Policy: same-origin
   Cross-Origin-Embedder-Policy: require-corp
   ```

4. **Corps des erreurs 4xx/5xx** non lisible via `fetch`. Si un écran a besoin
   du détail d'erreur, faire renvoyer un `200` + champ d'état dans le corps
   plutôt qu'un code HTTP d'erreur.

## Construire le build web

Depuis le SDK Ren'Py (≥ 7.3) : lanceur → **Build → Web**, ou en ligne de
commande. Le build produit un dossier servi par n'importe quel serveur web
(avec les en-têtes COOP/COEP du point 3).
