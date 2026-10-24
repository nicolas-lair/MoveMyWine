# Import Baqio — révision 2 Implementation Plan

> **For agentic workers:** tests écrits par un agent distinct de l'implémenteur ;
> l'implémenteur ne modifie jamais les tests.

**Goal:** Pré-charger les 50 commandes non facturées les plus récentes, sélection par un
seul multiselect, correspondance de destination par code postal, répartition affichée
avant le tarif total.

**Spec:** `docs/superpowers/specs/2026-10-24-baqio-import-design.md` (révision 2).

## Global Constraints

- Aucune donnée client réelle dans le dépôt (fixtures anonymisées, `test/baqio/factories.py`).
- Une erreur Baqio ne bloque jamais la saisie manuelle.
- Clés de widget : `baqio_selected`, `baqio_main`, `baqio_refresh` (`baqio_load` supprimé en task 4).
  `baqio_query` et `baqio_search` disparaissent.
- Messages conservés : MSG_AUTH, MSG_UNAVAILABLE, MSG_NO_RESULT, MSG_NO_BOTTLE,
  MSG_OUT_OF_RANGE, MSG_IGNORED, MSG_MIXED_ADDRESSES, MSG_INVALID_ORDER, MSG_MANUAL_EDIT.
  MSG_EMPTY_QUERY est supprimé.

## Interfaces

- `src/baqio/client.py` : `RECENT_ORDERS_PARAMS: list[tuple[str, str]]` =
  `[("q[state_in][]", "pending"), ("q[state_in][]", "validated"), ("q[s]", "created_at desc")]` ;
  `BaqioClient.recent_orders() -> list[dict]`. `build_search_params` et `search_orders`
  sont supprimés.
- `src/baqio/destination.py` : `match_destination(df_postal_code, zip, city, country)`
  inchangé en signature ; nouvelle règle (spec, « Correspondance destination »).
  `postal_code_of(key: str) -> str` extrait le code postal d'une entrée Destination
  (`key.split(" - ")[0].strip()`).
- `src/baqio/app.py` : `baqio_import(df_postal_code)` pré-charge une fois par session
  (`session_state.baqio_loaded_once`), bouton `baqio_refresh` (callback) recharge.
- `src/streamlit_app.py` : `display_group_split()` appelé après `cost_callback()` et avant
  `display_result(result)`.

## Task 1 — Tests (agent tests)

- `test/baqio/test_client.py` : `recent_orders` envoie exactement `RECENT_ORDERS_PARAMS`
  (aucun paramètre `q[name_or_customer_name_cont]`) ; mapping des erreurs conservé.
- `test/baqio/test_destination.py` : `"75011"` + ville `"Paris"` avec une seule entrée
  `75011 - Paris 11` → cette clé, `warning is None` ; plusieurs communes, ville trouvée
  (avec accents) → sans avertissement ; plusieurs communes, ville absente → première
  entrée + avertissement ; code postal absent ; hors France ; préférence sans lieu-dit ;
  `postal_code_of`.
- `test/test_app.py` : `FakeBaqioClient.recent_orders` compte ses appels ; un seul appel
  sur plusieurs reruns ; nouvel appel après clic sur `baqio_refresh` ; liste vide →
  MSG_NO_RESULT ; erreurs auth / indisponible → messages, app utilisable ; options du
  multiselect triées par date décroissante, commandes invalides écartées ; une commande
  sélectionnée reste en option après un refresh qui ne la renvoie plus ; parcours de
  chargement existants adaptés ; tableau de répartition rendu avant le montant
  « € HT » de `display_result`.

## Task 2 — Implémentation (contrôleur)

Implémenter les interfaces ci-dessus jusqu'à ce que `uv run pytest` passe, puis
`ruff check`, `ruff format`, `pre-commit run --all-files`. Mettre à jour la section Baqio
de `CLAUDE.md` si nécessaire.

## Task 3 — Commande hors des 50 (option 1)

Interfaces :
- `src/baqio/client.py` : `build_search_params(text: str) -> list[tuple[str, str]]` =
  `RECENT_ORDERS_PARAMS + [("q[name_or_customer_name_cont]", text)]` ;
  `BaqioClient.search_orders(text: str) -> list[dict]`.
- `src/baqio/app.py` : multiselect `baqio_selected` avec `accept_new_options=True` et
  `on_change=_resolve_typed`. Constantes `MSG_SEARCH_NO_RESULT =
  "Aucune commande non facturée pour « {text} »."` et `MSG_SEARCH_CHOOSE =
  "{count} commandes trouvées pour « {text} » — ajoutées à la liste, sélectionnez-les."`.
  Les valeurs de `baqio_selected` hors callback sont toujours des ids `int`.

Tests (agent tests, écrits **avant** l'implémentation, doivent échouer d'abord) :
client (`search_orders` params, `build_search_params`) et app (cas listés dans la spec,
section Tests). Si `AppTest` ne permet pas de saisir une nouvelle option, tester
`_resolve_typed` en appelant le callback via la valeur de session et le documenter.

## Task 4 — Chargement dynamique

Interfaces :
- `src/baqio/app.py` : suppression du bouton `baqio_load`. `_on_selection_change()`
  (on_change du multiselect) = `_resolve_typed()` puis `_load_selection(df_postal_code)` ;
  `_load_selection` est aussi l'`on_change` du radio `baqio_main`. `df_postal_code` est
  passé par `args=`. Bouton `baqio_refresh` libellé « Recharger Baqio ».
- Sélection vide → `baqio_group = None`, champs inchangés ; échec → `baqio_group = None`.

Tests (agent tests, avant implémentation) : les parcours qui cliquaient `baqio_load`
chargent désormais sur `set_value` du multiselect / du radio ; changement du destinataire
principal → nouvelle destination ; ajout d'une 2e commande → totaux mis à jour ;
désélection complète → champs inchangés, pas de tableau ; échec de chargement après un
groupe valide → `baqio_group is None` ; bouton `baqio_load` absent.

## Task 5 — Catalogue produits en arrière-plan

Interfaces :
- `src/baqio/client.py` : `MAX_VARIANT_PAGES = 20` ;
  `BaqioClient.all_product_variants() -> dict[int, dict]` (pages 1.. jusqu'à une page
  vide ou `MAX_VARIANT_PAGES`, paramètre `[("page", str(n))]`, erreurs typées comme les
  autres appels).
- `src/baqio/app.py` : `CATALOG_TIMEOUT = 10` (secondes) ; `_start_catalog(client)`
  soumet `client.all_product_variants` à un `ThreadPoolExecutor` module et stocke le
  `Future` dans `session_state.baqio_catalog` ; appelé par `_refresh_orders` après un
  pré-chargement réussi. `_fetch_variants` intègre d'abord le catalogue (`future.result(
  timeout=CATALOG_TIMEOUT)`), puis `baqio_catalog = None` ; exception → `None`, repli ;
  `TimeoutError` → `Future` conservé, repli.

Tests (agent tests, avant implémentation) :
- client : pagination jusqu'à page vide, plafond de pages, indexation par id, erreurs.
- app (FakeBaqioClient avec `all_product_variants`, compteurs d'appels) : catalogue
  demandé une fois au pré-chargement ; sélection d'une commande dont les variantes sont
  au catalogue → aucun `get_product_variant` ; variante absente du catalogue → un appel
  unitaire ; catalogue en erreur → repli unitaire, chargement réussi, aucun message
  d'erreur ; « Recharger Baqio » relance le catalogue.
