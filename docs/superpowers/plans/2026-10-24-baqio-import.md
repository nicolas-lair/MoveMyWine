# Import de commandes Baqio — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pré-remplir bouteilles / magnums / destination depuis une ou plusieurs commandes Baqio non facturées et répartir le coût d'une expédition groupée au prorata de l'équivalent 75 cl.

**Architecture:** Nouveau package `src/baqio/` en quatre unités : `client.py` (HTTP seul), `order.py` (parsing pur + répartition), `destination.py` (correspondance adresse → entrée `df_postal_code`, pur), `app.py` (widget Streamlit + messages). Le calcul de coût existant n'est pas modifié ; le widget écrit seulement dans `st.session_state` avant le rendu des champs.

**Tech Stack:** Python 3.11/3.12, Streamlit ~1.54 (`AppTest` pour les tests UI), pandas, `requests`, pytest, uv, ruff.

**Spec:** `docs/superpowers/specs/2026-10-24-baqio-import-design.md`

## Execution Protocol — tests et implémentation par des agents distincts

Exigence utilisateur : **les tests sont rédigés par un autre agent que celui qui implémente.**
Pour chaque tâche 2 à 6 :

1. **Agent « tests »** (frais) — reçoit : la spec, la section *Global Constraints*, et de la
   tâche uniquement *Files*, *Interfaces* et l'étape *Tests*. Il écrit les tests, crée les
   modules cibles avec les signatures vides seulement si nécessaire à la collecte
   (`raise NotImplementedError`), vérifie qu'ils **échouent** pour la bonne raison, et
   commite (`test: ...`). Il ne lit pas d'implémentation existante de la tâche.
2. **Agent « implémentation »** (frais, différent) — reçoit la tâche entière. Il rend les
   tests verts **sans modifier les fichiers de test**. S'il juge un test faux ou contraire à
   la spec, il s'arrête et le signale au contrôleur (qui tranche, éventuellement en
   renvoyant à l'agent « tests »). Il commite (`feat: ...`).
3. **Agent « revue »** — vérifie la conformité spec + tâche, puis le contrôleur passe à la
   tâche suivante.

La tâche 1 (vérification de l'API réelle) est conduite par le contrôleur avec l'utilisateur,
qui seul détient les clés.

## Global Constraints

- Ne jamais lire `.streamlit/secrets.toml` ni demander les clés dans la conversation.
- Aucune donnée client réelle dans le dépôt (public) : fixtures anonymisées uniquement.
- Base URL par défaut : `https://app.baqio.com/api/v1` ; auth HTTP Basic (`user`, `password`).
- États de commande retenus : `pending` et `validated` uniquement.
- Classement d'une ligne via `product_size` de `GET /product_variants/{id}` : `kind == "bottle"` et `milliliters == 750` → bouteille ; `kind == "bottle"` et `milliliters == 1500` → magnum ; tout le reste → ligne ignorée.
- Prorata : `bottles + 2 * magnums` ; parts arrondies au centime, la dernière absorbe l'écart, somme == total.
- Le transporteur de la commande Baqio n'est **pas** utilisé.
- Sans section `[baqio]` dans `st.secrets` (ou sans fichier de secrets), l'app est strictement inchangée.
- Une erreur Baqio ne doit jamais empêcher la saisie et le calcul manuels.
- `test/test_app.py` reste vert à chaque commit ; ne jamais passer `--no-verify` (pre-commit exporte `requirements.txt`).
- Lint/format : `ruff check src/ test/` et `ruff format src/ test/` propres.

## Review Focus

1. **Groupe trop gros pour les champs** (> 1200 bouteilles ou > 100 magnums, limites des `number_input`) → chargement refusé avec `MSG_OUT_OF_RANGE`, champs inchangés. Test : tâche 5.
2. **Quantité non entière sur une ligne 75 cl / 1,5 l** (ex. `"13.5"`) → ligne ignorée, pas d'arrondi silencieux. Test : tâche 2.
3. **Commande sans client ou sans `shipping_information`/`billing_information`** (`None`) → pas d'exception, adresse `None`, destination inchangée avec `MSG_NO_ADDRESS`. Tests : tâches 2 et 4.
4. **Nouvelle recherche après sélection** → les commandes déjà sélectionnées restent sélectionnées et affichées. Test : tâche 5.
5. **Plusieurs entrées `df_postal_code` pour la même commune** (lieux-dits) → on retient l'entrée sans lieu-dit si elle existe. Test : tâche 4.

---

### Task 1: Vérifier le filtre de recherche sur l'API réelle (contrôleur + utilisateur)

**Files:**
- Create (hors dépôt) : `<scratchpad>/probe/baqio_probe4.py`, réutilisant `get()` de `baqio_probe.py`

- [ ] **Step 1: Écrire le script** qui affiche, pour chaque variante, le nombre de résultats et les `name` / `customer.name` / `state` / `created_at` des 5 premiers :
  - `q[name_or_customer_name_cont]=<texte>` avec un nom de client connu, puis avec un nom de commande (`#9001`) ;
  - `q[name_cont]=<texte>` et `q[customer_name_cont]=<texte>` séparément ;
  - `q[state_in][]=pending&q[state_in][]=validated` ;
  - `q[s]=created_at desc`.
- [ ] **Step 2: Faire lancer le script par l'utilisateur** (PowerShell séparé, variables d'environnement `BAQIO_USER` / `BAQIO_PASSWORD`).
- [ ] **Step 3: Fixer `build_search_params` (tâche 3)** et l'écrire dans ce plan, en remplaçant la valeur par défaut ci-dessous si nécessaire :
  - filtre combiné appliqué → défaut conservé ;
  - sinon → `search_orders` fait deux requêtes (`q[name_cont]`, `q[customer_name_cont]`), fusionne et dédoublonne par `id` ; mettre à jour le test correspondant de la tâche 3 avant de la lancer.
  Le tri est de toute façon refait côté app (tâche 5), `q[s]` est seulement conservé s'il est accepté.

---

### Task 2: `order.py` — parsing des commandes et répartition

**Files:**
- Create: `src/baqio/__init__.py` (vide), `src/baqio/order.py`
- Test: `test/baqio/__init__.py`, `test/baqio/factories.py`, `test/baqio/test_order.py`

**Interfaces:**
- Produces (`src/baqio/order.py`) :
  ```python
  BOTTLE_ML = 750
  MAGNUM_ML = 1500

  @dataclass(frozen=True)
  class IgnoredLine:
      description: str   # f"{line['name']} — {line['description']}" (parties absentes omises)
      quantity: float

  @dataclass(frozen=True)
  class BaqioOrder:
      id: int
      name: str            # "#9001"
      customer: str        # customer.name, "" si absent
      created_at: datetime # datetime.fromisoformat(raw["created_at"])
      bottles: int
      magnums: int
      zip: str | None
      city: str | None
      country: str | None  # country_code
      ignored_lines: tuple[IgnoredLine, ...]
      @property
      def bottle_equivalent(self) -> int: ...   # bottles + 2 * magnums

  def variant_ids(raw: dict) -> set[int]          # product_variant_id des order_lines_not_deleted (None exclus)
  def parse_order(raw: dict, variants: Mapping[int, dict | None]) -> BaqioOrder
  def order_label(raw: dict) -> str               # "#9001 · Cave Exemple · BORDEAUX · 23/09 · 36 btl"
  def split_cost(total: float, orders: Sequence[BaqioOrder]) -> list[float]
  ```
- Produces (`test/baqio/factories.py`, utilisé par les tâches 5 et 6) :
  `make_line(variant_id, quantity, name="Cuvée", description="Bouteille (75 cl)") -> dict`,
  `make_order(id=1, name="#1", customer="Client A", lines=(), zip="33000", city="BORDEAUX", country="FR", use_billing_address=False, created_at="2026-09-21T13:25:41.634+02:00", bottle_quantity="0.0") -> dict`
  (structure réelle : `customer.shipping_information` / `customer.billing_information`, `order_lines_not_deleted`, `quantity` en chaîne `"24.0"` ; avec `use_billing_address=True` l'adresse est placée dans `billing_information` et `shipping_information` a des champs `None`),
  `make_variant(id, milliliters=750, kind="bottle") -> dict` (avec `product_size = {"id": ..., "name": ..., "milliliters": ..., "kind": ...}`).
  Données inventées uniquement.

- [ ] **Step 1: Tests (agent « tests »)** — `test/baqio/test_order.py` :
  - `test_classifies_bottles_and_magnums` : lignes 24 × variante 750 ml + 6 × variante 1500 ml → `bottles == 24`, `magnums == 6`, `bottle_equivalent == 36`, `ignored_lines == ()`.
  - `test_ignores_other_formats` : variante `kind="bulk"` 13.56, variante `kind="bottle"` 375 ml, variante `kind="bib"`, ligne sans `product_variant_id`, variante absente du mapping (`None`) → 5 `IgnoredLine` avec leurs quantités, `bottles == magnums == 0`.
  - `test_ignores_non_integer_quantity` (Review Focus 2) : variante 750 ml quantité `"13.5"` → ignorée, `bottles == 0`.
  - `test_shipping_address` : `zip`, `city`, `country` lus dans `shipping_information`.
  - `test_billing_address_fallback` : `use_billing_address=True` → adresse de `billing_information`.
  - `test_missing_customer_or_address` (Review Focus 3) : `customer=None`, puis `shipping_information=None` et `billing_information=None` → pas d'exception, `zip is city is country is None`, `customer == ""`.
  - `test_variant_ids` : renvoie l'ensemble des ids, sans `None`.
  - `test_order_label` : `make_order(name="#9001", customer="Cave Exemple", city="BORDEAUX", created_at="2026-09-23T10:00:00+02:00", bottle_quantity="36.0")` → `"#9001 · Cave Exemple · BORDEAUX · 23/09 · 36 btl"`.
  - `test_split_cost_prorata` : équivalents 36, 12 (6 magnums), 24 ; total 100.0 → `[50.0, 16.67, 33.33]` ; `sum == 100.0`.
  - `test_split_cost_rounding_absorbed_by_last` : 3 commandes de 1 équivalent, total 10.0 → `[3.33, 3.33, 3.34]`.
  - `test_split_cost_single_order` : `[42.5]` pour total 42.5.
  - `test_split_cost_zero_equivalent_raises` : `ValueError`.
- [ ] **Step 2: Vérifier l'échec** — `uv run pytest test/baqio/test_order.py -v` → FAIL (`ImportError` / `NotImplementedError`). Commit `test: add Baqio order parsing tests`.
- [ ] **Step 3: Implémenter `src/baqio/order.py` (agent « implémentation »)** — adresse : `shipping_information`, ou `billing_information` si `shipping_information.use_billing_address` est vrai ; tout niveau `None` → champs `None`. Quantité : `float(q)`, ligne comptée seulement si `q.is_integer()`. Libellé : date `created_at` au format `%d/%m`, bouteilles `int(float(raw["bottle_quantity"]))`, ville omise (avec son séparateur) si absente. `split_cost` : `round(total * eq / total_eq, 2)` pour toutes les parts sauf la dernière, dernière = `round(total - sum(autres), 2)`.
- [ ] **Step 4: Vérifier** — `uv run pytest test/baqio/test_order.py -v` → PASS ; `ruff check src/ test/` propre.
- [ ] **Step 5: Commit** — `git add src/baqio test/baqio && git commit -m "feat: parse Baqio orders and split group cost"`

---

### Task 3: `client.py` — client HTTP Baqio

**Files:**
- Create: `src/baqio/client.py`
- Modify: `pyproject.toml` (via `uv add "requests>=2.32,<3"`), `uv.lock`, `requirements.txt` (régénéré par pre-commit)
- Test: `test/baqio/test_client.py`

**Interfaces:**
- Produces :
  ```python
  DEFAULT_BASE_URL = "https://app.baqio.com/api/v1"
  class BaqioError(Exception)
  class BaqioAuthError(BaqioError)          # 401, 403
  class BaqioUnavailableError(BaqioError)   # requests.ConnectionError / Timeout, 5xx, autre 4xx non géré

  def build_search_params(text: str) -> list[tuple[str, str]]

  class BaqioClient:
      def __init__(self, user: str, password: str, base_url: str = DEFAULT_BASE_URL, timeout: float = 15.0)
      def search_orders(self, text: str) -> list[dict]          # GET {base_url}/orders, liste JSON brute
      def get_product_variant(self, variant_id: int) -> dict | None   # GET {base_url}/product_variants/{id} ; 404 → None
  ```
  Tous les appels passent par `requests.get(url, params=..., auth=(user, password), headers={"Accept": "application/json"}, timeout=timeout)` (les tests patchent `src.baqio.client.requests.get`).
- `build_search_params("dupont")` par défaut (à ajuster selon la tâche 1) :
  `[("q[name_or_customer_name_cont]", "dupont"), ("q[state_in][]", "pending"), ("q[state_in][]", "validated"), ("q[s]", "created_at desc")]`

- [ ] **Step 1: Tests (agent « tests »)** — `test/baqio/test_client.py`, avec un faux `requests.get` qui enregistre ses arguments et renvoie un objet `status_code` / `json()` :
  - `test_build_search_params` : égalité exacte avec la liste ci-dessus.
  - `test_search_orders_request` : URL `https://app.baqio.com/api/v1/orders`, `params == build_search_params("dupont")`, `auth == ("u", "p")`, `timeout` présent ; renvoie la liste JSON.
  - `test_custom_base_url` : `base_url="https://demo.baqio.com/api/v1"` → URL démo.
  - `test_get_product_variant` : URL `.../product_variants/222206`, renvoie le dict.
  - `test_get_product_variant_404_returns_none`.
  - `test_auth_errors` (paramétré 401, 403) → `BaqioAuthError`.
  - `test_server_error` (500, 503) → `BaqioUnavailableError`.
  - `test_network_errors` : `requests.ConnectionError`, `requests.Timeout` levées par `get` → `BaqioUnavailableError`.
- [ ] **Step 2: Vérifier l'échec** — `uv run pytest test/baqio/test_client.py -v` → FAIL. Commit `test: add Baqio client tests`.
- [ ] **Step 3: Implémenter** — `uv add "requests>=2.32,<3"`, puis `src/baqio/client.py` selon *Interfaces*.
- [ ] **Step 4: Vérifier** — `uv run pytest test/baqio -v` → PASS.
- [ ] **Step 5: Commit** — `git add pyproject.toml uv.lock requirements.txt src/baqio/client.py && git commit -m "feat: add Baqio HTTP client"` (pre-commit doit régénérer `requirements.txt` ; l'ajouter si modifié et recommiter).

---

### Task 4: `destination.py` — adresse Baqio → entrée `df_postal_code`

**Files:**
- Create: `src/baqio/destination.py`
- Test: `test/baqio/test_destination.py`

**Interfaces:**
- Consumes: `PostalCodeAPI.Cols` (`src/app_generics/postal_code.py`) — colonnes `Code_postal`, `Nom_de_la_commune`, `Ligne_5` ; index = clé du selectbox `destination`.
- Produces :
  ```python
  @dataclass(frozen=True)
  class DestinationMatch:
      key: str | None       # index de df_postal_code ; None = destination inchangée
      warning: str | None

  def normalize_city(name: str) -> str   # sans accents, majuscules, "-" et "'" → espace, espaces multiples réduits, strip
  def match_destination(df_postal_code: pd.DataFrame, zip: str | None, city: str | None, country: str | None) -> DestinationMatch
  ```
- Messages exacts (constantes du module) :
  - `MSG_NO_ADDRESS = "Adresse de livraison absente — destination inchangée."`
  - `MSG_NOT_FRANCE = "Adresse hors de France ({country}) — destination inchangée."`
  - `MSG_ZIP_NOT_FOUND = "Code postal {zip} introuvable — destination inchangée."`
  - `MSG_CITY_NOT_FOUND = "Commune « {city} » introuvable pour le code postal {zip} — « {key} » retenue, à vérifier."`
- Règles : `zip` absent → `MSG_NO_ADDRESS` ; `country` non vide et ≠ `"FR"` → `MSG_NOT_FRANCE` ; pas de ligne pour le code postal → `MSG_ZIP_NOT_FOUND` ; parmi les lignes du code postal, celles dont `normalize_city(commune) == normalize_city(city)`, en préférant une ligne sans lieu-dit (`Ligne_5` vide ou NaN), sinon la première → `warning=None` ; aucune commune correspondante → première ligne du code postal + `MSG_CITY_NOT_FOUND`.

- [ ] **Step 1: Tests (agent « tests »)** — `test/baqio/test_destination.py`, sur un petit `DataFrame` construit comme `get_postal_code_df` (index `"cp - commune - lieudit"`, les trois colonnes), communes inventées ou publiques :
  - `test_normalize_city` : `"Lège-Cap-Ferret"` et `"LEGE CAP FERRET"` → même valeur ; `"L'Isle-d'Abeau"` → `"L ISLE D ABEAU"`.
  - `test_exact_match` : `("33950", "LEGE-CAP-FERRET", "FR")` → clé de Lège-Cap-Ferret, `warning is None`.
  - `test_prefers_entry_without_lieudit` (Review Focus 5) : deux lignes même code postal et commune, l'une avec lieu-dit (placée en premier) → clé de la ligne sans lieu-dit.
  - `test_several_communes_same_zip` : la commune demandée n'est pas la première du code postal → c'est bien elle qui est retenue.
  - `test_city_not_found` : → première ligne du code postal, `warning == MSG_CITY_NOT_FOUND.format(...)`.
  - `test_zip_not_found`, `test_not_france` (`"BE"`), `test_missing_zip` (`None`) → `key is None` et le message correspondant.
  - `test_country_none_treated_as_france` : `country=None`, code postal présent → correspondance normale.
- [ ] **Step 2: Vérifier l'échec** — `uv run pytest test/baqio/test_destination.py -v` → FAIL. Commit `test: add Baqio destination matching tests`.
- [ ] **Step 3: Implémenter** `src/baqio/destination.py` (`unicodedata.normalize("NFKD", ...)` puis suppression des caractères combinants).
- [ ] **Step 4: Vérifier** — `uv run pytest test/baqio -v` → PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat: match Baqio address to postal code entry"`

---

### Task 5: Widget « Importer depuis Baqio » (recherche, sélection, chargement)

**Files:**
- Create: `src/baqio/app.py`
- Modify: `src/streamlit_app.py` (appel du widget juste après `st.markdown("#### Expédition")`, avant `destination_city_input`)
- Modify: `test/test_app.py` (`mock_postal_code_retriever` : ajouter les colonnes `Nom_de_la_commune` et `Ligne_5` sans changer index ni codes postaux existants, plus une entrée `"33000 - Bordeaux"` ; nouveaux tests)
- Modify: `CLAUDE.md` (section « Baqio » : package `src/baqio/`, format des secrets `[baqio] user / password / base_url`)

**Interfaces:**
- Consumes: `BaqioClient`, `BaqioAuthError`, `BaqioUnavailableError` (tâche 3) ; `BaqioOrder`, `parse_order`, `variant_ids`, `order_label`, `split_cost` (tâche 2) ; `match_destination` (tâche 4).
- Produces (`src/baqio/app.py`) :
  ```python
  def baqio_enabled() -> bool          # "baqio" in st.secrets ; toute exception (pas de fichier de secrets) → False
  def get_client() -> BaqioClient      # user, password, base_url (optionnel → DEFAULT_BASE_URL) depuis st.secrets["baqio"] ; les tests le monkeypatchent
  def baqio_import(df_postal_code: pd.DataFrame) -> None   # ne rend rien si not baqio_enabled()

  @dataclass(frozen=True)
  class LoadedGroup:
      orders: tuple[BaqioOrder, ...]   # destinataire principal en premier
      bottles: int
      magnums: int
  ```
  Clés `session_state` : `baqio_query` (text_input), `baqio_orders: dict[int, dict]` (commandes brutes vues, par id), `baqio_results: list[int]` (ids de la dernière recherche), `baqio_selected` (multiselect d'ids), `baqio_main` (radio d'id), `baqio_variants: dict[int, dict | None]` (cache de session ; **pas** `st.cache_data`, pour éviter les fuites entre tests et entre comptes), `baqio_group: LoadedGroup | None`, `baqio_messages: list[tuple[str, str]]` (niveau `"error" | "warning" | "info"`, texte), rendus dans l'expander.
- Messages exacts (constantes de `src/baqio/app.py`) :
  - `EXPANDER_LABEL = "📦 Importer depuis Baqio"`
  - `MSG_AUTH = "Identifiants Baqio invalides."`
  - `MSG_UNAVAILABLE = "Baqio indisponible — saisie manuelle possible."`
  - `MSG_NO_RESULT = "Aucune commande non facturée trouvée."`
  - `MSG_EMPTY_QUERY = "Saisissez un numéro de commande ou un nom de client."`
  - `MSG_NO_BOTTLE = "Aucune bouteille 75 cl ni magnum dans les commandes sélectionnées."`
  - `MSG_OUT_OF_RANGE = "Quantités hors limites de l'app (max 1200 bouteilles, 100 magnums) — chargement annulé."`
  - `MSG_IGNORED = "Lignes ignorées ({order}) : {lines}"` (`lines` = `"{description} × {quantité}"` séparées par `", "`)
  - `MSG_MIXED_ADDRESSES = "Adresses différentes dans le groupe : destination = adresse de {customer}."`
- Comportement :
  - Bouton « Rechercher » (callback) : requête vide → `MSG_EMPTY_QUERY` sans appel ; sinon `search_orders`, mise à jour de `baqio_orders` / `baqio_results`, résultats vides → `MSG_NO_RESULT`.
  - Options du multiselect = `baqio_results` ∪ `baqio_selected`, sans doublon, triées par `created_at` décroissant, `format_func=order_label`.
  - Radio « Destinataire principal » seulement si au moins 2 commandes sélectionnées ; défaut = première sélectionnée ; `baqio_main` remis sur la première sélectionnée s'il n'est plus dans la sélection.
  - Bouton « Charger » (callback `on_click`, `args=(df_postal_code,)`, désactivé sans sélection) : récupère les variantes absentes de `baqio_variants`, parse, puis dans l'ordre : `MSG_NO_BOTTLE` si équivalent total nul → rien n'est écrit ; `MSG_OUT_OF_RANGE` si bouteilles > 1200 ou magnums > 100 → rien n'est écrit ; sinon écrit `bottle`, `magnum`, `baqio_group`, et `destination` si `match_destination(...).key` n'est pas `None` ; ajoute les messages `MSG_IGNORED` (warning, un par commande concernée), avertissement de destination (warning), `MSG_MIXED_ADDRESSES` (info, si les `(zip, city)` diffèrent).
  - `BaqioAuthError` → `MSG_AUTH` (error) ; `BaqioUnavailableError` → `MSG_UNAVAILABLE` (warning) ; dans les deux cas aucune clé de saisie n'est modifiée.
  - `baqio_messages` est vidé au début de chaque callback.

- [ ] **Step 1: Tests (agent « tests »)** — dans `test/test_app.py`, une classe `TestBaqioImport` ; `FakeBaqioClient` (commandes et variantes construites avec `test/baqio/factories.py`, compteur d'appels, option pour lever une exception) injecté par `monkeypatch.setattr(src.baqio.app, "get_client", ...)` ; secrets via `app.secrets["baqio"] = {"user": "u", "password": "p"}` ; indicateurs et codes postaux mockés comme dans `_build_app` :
  - `test_hidden_without_secrets` : aucun expander de label `EXPANDER_LABEL`, aucune exception.
  - `test_empty_query` : « Rechercher » sans texte → `MSG_EMPTY_QUERY`, 0 appel à `search_orders`.
  - `test_search_no_result` → `MSG_NO_RESULT`.
  - `test_load_single_order` : commande 24 × 75 cl + 3 × 1,5 l à `33000 BORDEAUX` → après « Charger » : `bottle == 24`, `magnum == 3`, `destination == "33000 - Bordeaux"`, pas de radio « Destinataire principal », coût calculé (`session_state.cost > 0`).
  - `test_load_group_main_recipient` : 2 commandes (`33000 BORDEAUX` 12 btl, `69001 LYON 01` 6 magnums), destinataire principal = la seconde → `bottle == 12`, `magnum == 6`, `destination == "69001 - Lyon 01"`, info `MSG_MIXED_ADDRESSES` avec le client de la seconde.
  - `test_selection_kept_across_searches` (Review Focus 4) : sélection d'une commande, nouvelle recherche qui ne la renvoie pas → elle est toujours dans `baqio_selected` et dans les options.
  - `test_ignored_lines_warning` : commande avec une ligne vrac → warning commençant par `"Lignes ignorées (#"`.
  - `test_no_bottle_refused` : seulement du vrac → `MSG_NO_BOTTLE`, `bottle` / `magnum` inchangés.
  - `test_out_of_range_refused` (Review Focus 1) : 1206 bouteilles → `MSG_OUT_OF_RANGE`, `bottle` inchangé, pas d'exception.
  - `test_unknown_zip_keeps_destination` (Review Focus 3) : code postal absent du mock → destination inchangée, warning `MSG_ZIP_NOT_FOUND` formaté.
  - `test_auth_error` / `test_unavailable` : le client lève → `MSG_AUTH` (error) / `MSG_UNAVAILABLE` (warning), saisie manuelle de `bottle` puis calcul toujours fonctionnels.
  - `test_variants_cached` : deux chargements de la même commande → `get_product_variant` appelé une fois par variante.
  - Le test `test_app` existant passe sans modification de ses assertions.
- [ ] **Step 2: Vérifier l'échec** — `uv run pytest test/test_app.py -v` → nouveaux tests FAIL, anciens PASS. Commit `test: add Baqio import UI tests`.
- [ ] **Step 3: Implémenter** `src/baqio/app.py`, l'appel dans `src/streamlit_app.py`, et la section `CLAUDE.md`.
- [ ] **Step 4: Vérifier** — `uv run pytest -v` → tout PASS ; `ruff check src/ test/` propre.
- [ ] **Step 5: Commit** — `git commit -m "feat: import Baqio orders into the expedition form"`

---

### Task 6: Tableau « Répartition du groupe »

**Files:**
- Modify: `src/baqio/app.py`, `src/streamlit_app.py` (appel dans `tab1`, juste après `display_result(result)`)
- Test: `test/test_app.py` (classe `TestBaqioImport`)

**Interfaces:**
- Consumes: `LoadedGroup`, `st.session_state.baqio_group`, `st.session_state.cost`, `st.session_state.tarif_unavailable`, `split_cost` (tâche 2).
- Produces :
  ```python
  SPLIT_TITLE = "#### Répartition du groupe"
  MSG_MANUAL_EDIT = "Quantités modifiées manuellement — répartition désactivée."
  SPLIT_COLUMNS = ["Commande", "Client", "Éq. 75 cl", "Part (%)", "Montant HT (€)"]
  def display_group_split() -> None
  ```
- Comportement : rien si `baqio_group` est `None` ou contient moins de 2 commandes ; `MSG_MANUAL_EDIT` (info) si `bottle` / `magnum` diffèrent de `baqio_group.bottles` / `.magnums` ; rien si tarif indisponible ou `cost == 0` ; sinon `SPLIT_TITLE` + `st.dataframe` aux colonnes `SPLIT_COLUMNS`, une ligne par commande dans l'ordre de `baqio_group.orders`, montants = `split_cost(cost, orders)`, part = `round(100 * eq / total_eq, 1)`. Changer la destination ou le transporteur ne désactive pas le tableau (montants recalculés).

- [ ] **Step 1: Tests (agent « tests »)** :
  - `test_split_table_for_group` : groupe de 2 commandes (24 btl et 12 btl, même destination) → dataframe aux colonnes `SPLIT_COLUMNS`, 2 lignes, somme des montants == `session_state.cost`, parts `66.7` / `33.3`.
  - `test_no_split_for_single_order`.
  - `test_split_disabled_after_manual_edit` : après chargement, `bottle` modifié → `MSG_MANUAL_EDIT`, pas de dataframe de répartition.
  - `test_split_follows_transporter_change` : changement de transporteur → somme des montants == nouveau `cost`.
- [ ] **Step 2: Vérifier l'échec** puis commit `test: add Baqio group split tests`.
- [ ] **Step 3: Implémenter** `display_group_split` et son appel.
- [ ] **Step 4: Vérifier** — `uv run pytest -v` → tout PASS ; `pre-commit run --all-files` propre.
- [ ] **Step 5: Commit** — `git commit -m "feat: show cost split for grouped Baqio orders"`

---

### Task 7: Vérification de bout en bout (contrôleur + utilisateur)

- [ ] **Step 1:** L'utilisateur ajoute `[baqio]` à `.streamlit/secrets.toml` (sans le montrer), lance `streamlit run src/streamlit_app.py`, recherche une commande réelle `pending`, charge un groupe de 2 commandes, et contrôle bouteilles / magnums / destination / répartition par rapport à Baqio.
- [ ] **Step 2:** L'utilisateur ajoute les secrets `[baqio]` sur Streamlit Cloud pour `develop` avant le merge de `feat/baqio-import` dans `develop`.
