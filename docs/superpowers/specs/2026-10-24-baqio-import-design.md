# Import de commandes Baqio — Design

Date : 2026-10-24 — révision 2 le 2026-10-24 après test sur données réelles
Branche : `feat/baqio-import`

Révision 2 (retours du test réel) :

- Une requête de recherche par commande à grouper était trop lente : les commandes
  sont **pré-chargées** (les 50 plus récentes) et filtrées localement par le champ de
  saisie du multiselect. Le champ texte et le bouton « Rechercher » disparaissent.
- La correspondance de destination se fait sur le **code postal** et non plus sur le nom
  de la commune (« Paris » ne correspondait pas à « Paris 11 » et levait un
  avertissement).
- Le tableau « Répartition du groupe » est affiché **avant** le tarif total.
- Une commande hors des 50 pré-chargées se retrouve en **validant le texte tapé** dans
  le multiselect (Entrée) : l'app interroge alors Baqio avec ce texte.
- Plus de bouton « Charger » : le formulaire est rempli **dès que la sélection change**.
- Le catalogue des produits est **pré-chargé en arrière-plan** : la classification des
  lignes ne coûte plus un appel par produit au moment de la sélection.

## Objectif

Pré-remplir les champs **Bouteilles**, **Magnums** et **Destination** de l'app à partir
d'une ou plusieurs commandes Baqio non facturées, et répartir le coût de transport entre
les commandes quand elles sont expédiées ensemble (expédition groupée).

Contexte métier :

- Dans Baqio, le prix de l'expédition doit être saisi **avant** de valider la commande ;
  la validation génère l'expédition automatiquement. On travaille donc sur les
  **commandes**, pas sur les expéditions.
- Une expédition groupée = plusieurs commandes (plusieurs clients) envoyées en un seul
  envoi vers **une seule destination**. Le transporteur ne voit qu'un envoi ; les clients
  s'arrangent ensuite entre eux.
- Chaque client paie au **prorata de son équivalent 75 cl** (1 magnum = 2 bouteilles),
  ce qui reflète la façon dont les transporteurs tarifent.
- L'app sert justement à choisir le transporteur : le transporteur de la commande Baqio
  n'est pas utilisé.

Hors périmètre (plus tard) :

- Écriture du prix dans Baqio (`PUT /orders/{id}`, champ `shipping_line.price_cents`).
- Chargement d'un groupe Baqio `EG-xx` : l'API publique ne l'expose pas (vérifié :
  `fulfillment_group_id` est `null` même pour les membres d'un groupe, et aucun endpoint
  `/fulfillment_groups`).
- Répartition dans l'onglet « Comparaison ».

## API Baqio (faits vérifiés)

Spec OpenAPI : `Baqio-Public-API.v1.json` du dépôt GitHub `Baqio/api-doc`. Faits
confirmés sur des données réelles par des scripts de sondage jetables.

- Base URL : `https://app.baqio.com/api/v1` (démo : `https://demo.baqio.com/api/v1`).
- Authentification : HTTP Basic.
- `GET /orders` : paginé par 50, filtres Ransack `q[<attribut>_<prédicat>]`. Un filtre
  sur un attribut inconnu est **ignoré silencieusement**.
- États de commande : `draft`, `pending` (devis), `validated` (pro forma), `removed`,
  `invoiced`, `cancelled`. On ne retient que `pending` et `validated`.
- Une commande contient :
  - `name` (ex. `#9001`), `created_at`, `state` ;
  - `customer.name` ;
  - `customer.shipping_information` (`zip`, `city`, `country_code`,
    `use_billing_address`) ; si `use_billing_address` est vrai, l'adresse est dans
    `customer.billing_information` ;
  - `order_lines_not_deleted[]` avec `product_variant_id`, `quantity`, `description`.
- `GET /product_variants/{id}` renvoie l'objet `product_size` complet (l'objet
  `product_variant` imbriqué dans les lignes n'a que `product_size_id`) :
  - `{"id": 2, "name": "Bouteille (75 cl)", "milliliters": 750, "kind": "bottle"}`
  - `{"id": 3, "name": "Magnum (1,5 l)", "milliliters": 1500, "kind": "bottle"}`
  - `kind` ∈ `bulk`, `bottle`, `bib`. Des lignes sans format existent.

## Architecture

Nouveau package `src/baqio/`, trois unités indépendantes.

### `src/baqio/client.py` — `BaqioClient`

Transport HTTP uniquement. Dépendance nouvelle : `requests`.

- Construit depuis `st.secrets["baqio"]` : `user`, `password`, `base_url` (optionnel,
  défaut production).
- Timeout sur chaque requête.
- Exceptions typées : `BaqioAuthError` (401/403), `BaqioUnavailableError` (erreur réseau,
  timeout, 5xx).
- `recent_orders() -> list[dict]` : un seul `GET /orders` avec
  - `q[state_in][]=pending&q[state_in][]=validated` ;
  - tri par `created_at` décroissant (`q[s]=created_at desc`) ;
  - aucun filtre texte.
  Seule la première page est utilisée : les **50 commandes non facturées les plus
  récentes**, ce qui couvre l'usage.
- `search_orders(text: str) -> list[dict]` : un seul `GET /orders` avec les mêmes
  paramètres que `recent_orders` plus `q[name_or_customer_name_cont]=<text>` (filtre
  vérifié côté serveur). Première page seulement. Sert uniquement à retrouver une
  commande hors des 50 pré-chargées.
- `all_product_variants() -> dict[int, dict]` : `GET /product_variants?page=N` pour
  N = 1, 2, … jusqu'à une page vide (au plus 20 pages), indexé par `id`. Chaque élément
  contient le `product_size` complet, comme l'appel unitaire.
- `get_product_variant(variant_id: int) -> dict` : `GET /product_variants/{id}`, mis en
  cache par id en `session_state` pour ne payer qu'un appel par produit distinct. Ne sert
  plus que de repli pour un produit absent du catalogue.

Vérifié sur données réelles (sondage) : 59 variantes sur une seule page, récupérées en
moins de 2 s ; `product_size` présent sur toutes les variantes qui ont un format (les
autres ont `product_size_id` nul, donc ignorées de toute façon) ; tous les produits des
commandes récentes figurent dans la liste.

Vérifié sur données réelles : le filtre d'état et le tri sont appliqués côté serveur.
L'app garde un filet de sécurité : elle écarte toute commande dont l'état n'est pas
`pending` ou `validated`.

### `src/baqio/order.py` — parsing pur

Aucun appel réseau, aucun import Streamlit.

```python
@dataclass(frozen=True)
class IgnoredLine:
    description: str
    quantity: float


@dataclass(frozen=True)
class BaqioOrder:
    id: int
    name: str  # "#9001"
    customer: str
    created_at: datetime
    bottles: int
    magnums: int
    zip: str | None
    city: str | None
    country: str | None
    ignored_lines: tuple[IgnoredLine, ...]

    @property
    def bottle_equivalent(self) -> int:  # bottles + 2 * magnums
        ...
```

- `parse_order(raw: dict, variants: dict[int, dict]) -> BaqioOrder`
  - Classement d'une ligne via `variants[product_variant_id]["product_size"]` :
    - `kind == "bottle"` et `milliliters == 750` → bouteilles ;
    - `kind == "bottle"` et `milliliters == 1500` → magnums ;
    - tout le reste (vrac, BIB, autre volume, pas de format, variante introuvable) →
      `ignored_lines`.
  - Adresse : `customer.shipping_information`, ou `customer.billing_information` si
    `use_billing_address` est vrai.
- `split_cost(total: float, orders: Sequence[BaqioOrder]) -> list[float]`
  - Parts au prorata de `bottle_equivalent`, arrondies au centime.
  - La dernière part absorbe l'écart d'arrondi : la somme vaut exactement `total`.

### `src/baqio/app.py` — widget Streamlit

Voir « Interface ». Contient la correspondance adresse → entrée de `df_postal_code` et
toute la gestion d'erreurs affichée à l'utilisateur.

## Interface

`st.expander("📦 Importer depuis Baqio")` en haut de la section « Expédition », au-dessus
des champs actuels. **Affiché uniquement si `st.secrets` contient une section `[baqio]`** ;
sinon l'app est strictement inchangée.

Contenu :

1. **Pré-chargement** : au premier affichage de l'app dans une session, `recent_orders`
   est appelé une fois et les commandes sont stockées en `session_state`. Les reruns
   suivants ne refont pas l'appel.
   Juste après, `all_product_variants` est lancé dans un **thread de fond**
   (`concurrent.futures`), sans bloquer l'affichage ; le `Future` est stocké en
   `session_state.baqio_catalog`. Le client HTTP est construit dans le thread principal
   (lecture de `st.secrets`) ; le thread n'appelle aucune API Streamlit.
   Au chargement d'une sélection, si le catalogue n'a pas encore été intégré, l'app
   attend son résultat au plus 10 s, puis l'intègre au cache des variantes. Catalogue en
   erreur ou pas prêt à temps → repli silencieux sur `get_product_variant` pour chaque
   produit manquant (un catalogue pas prêt reste attendu au chargement suivant).
   « Recharger Baqio » relance aussi le catalogue. Un bouton « Recharger Baqio » (clé `baqio_refresh`) relance
   le chargement, par exemple après la création d'une commande dans Baqio.
2. `st.multiselect` « Numéro de commande ou client » (clé `baqio_selected`), seul champ
   de sélection. La saisie dans le multiselect filtre les options côté navigateur, sans
   requête : le libellé contient le numéro et le client, ce qui permet de taper l'un ou
   l'autre. Libellé : `#9001 · Cave Exemple · Bordeaux · 23/09 · 36 btl`. Plus récente en
   premier. Une commande déjà sélectionnée reste dans les options même si elle ne figure
   plus dans la liste après « Recharger Baqio ».
   **Commande hors liste** : le multiselect accepte un texte libre
   (`accept_new_options=True`). Valider un texte qui n'est pas une option (Entrée)
   déclenche, dans le callback `on_change` du multiselect, `search_orders(texte)` :
   - le texte est toujours retiré de la sélection (ce n'est pas une commande) ;
   - les commandes trouvées (mêmes contrôles de validité et d'état que le
     pré-chargement) sont ajoutées aux options ;
   - sont sélectionnées automatiquement : les commandes dont le numéro est égal au texte
     (insensible à la casse, `#` facultatif), sinon l'unique résultat s'il n'y en a
     qu'un ;
   - sinon, plusieurs résultats → `st.info("{n} commandes trouvées pour « {texte} » —
     ajoutées à la liste, sélectionnez-les.")` ;
   - aucun résultat → `st.info("Aucune commande non facturée pour « {texte} ».")`.
   - Texte vide après `strip` → ignoré, sans appel.
3. `st.radio` « Destinataire principal » parmi les commandes sélectionnées (client, ville),
   par défaut la première sélectionnée. Affiché seulement à partir de 2 commandes.
4. **Chargement dynamique**, sans bouton : il a lieu dans les callbacks `on_change` du
   multiselect (après la résolution d'un texte tapé) et du radio « Destinataire
   principal » (un callback est nécessaire pour modifier des widgets déjà déclarés).
   À chaque changement, le groupe sélectionné est rechargé en entier ; le chargement :
   - récupère les variantes manquantes et parse chaque commande ;
   - écrit `st.session_state.bottle` et `st.session_state.magnum` = totaux du groupe ;
   - écrit `st.session_state.destination` = entrée de `df_postal_code` correspondant au
     destinataire principal ;
   - mémorise le groupe chargé dans `st.session_state.baqio_group` (commandes et
     quantités chargées) ;
   - affiche les avertissements : lignes ignorées, adresse introuvable, adresses
     différentes au sein du groupe (information, attendu pour un groupe).

Les champs restent modifiables après chargement, mais tout changement de sélection
les écrase avec les valeurs du nouveau groupe.

- Sélection vidée → `bottle`, `magnum` et `destination` inchangés,
  `baqio_group = None` (la répartition disparaît), messages effacés.
- Chargement refusé (commande illisible, hors limites, aucune bouteille, erreur Baqio) →
  champs inchangés, `baqio_group = None`, message. Le groupe affiché par la répartition
  correspond donc toujours à la sélection courante.

### Correspondance destination

La correspondance se fait sur le **code postal**. Chaque entrée du champ Destination
(index de `df_postal_code`, au format `CP - Commune[ - Lieu-dit]`) commence par son code
postal : on extrait ce code de l'entrée et on le compare au `zip` de la commande.

1. Adresse absente, ou pays différent de `FR` → destination inchangée + avertissement.
2. Aucune entrée avec ce code postal → destination inchangée + avertissement.
3. Une seule commune pour ce code postal (cas de Paris, Lyon, Marseille et de la
   plupart des codes) → cette commune, **sans avertissement**, quel que soit le nom de
   ville saisi dans Baqio. Entre plusieurs entrées de cette commune, on préfère celle
   sans lieu-dit.
4. Plusieurs communes pour ce code postal → le nom de ville sert seulement à départager
   (nom normalisé : sans accents, majuscules, tirets et apostrophes remplacés par des
   espaces). Commune trouvée → retenue sans avertissement. Sinon → première entrée +
   avertissement « à vérifier ».

### Répartition

Onglet « Tarif détaillé », juste après le bloc « Surcharges » et **avant** le tarif
total (montant HT et détail du coût) : tableau « Répartition du groupe » — commande,
client, éq. 75 cl, part (%), montant HT — affiché seulement si au moins 2 commandes sont
chargées et que le coût est disponible.

Si `bottle` ou `magnum` diffèrent des quantités chargées (modification manuelle), le
tableau est masqué et remplacé par « Quantités modifiées manuellement — répartition
désactivée ». Une modification de la destination ne désactive pas la répartition.

## Secrets

`.streamlit/secrets.toml` en local (déjà ignoré par git) et secrets Streamlit Cloud pour
`main` et `develop` :

```toml
[baqio]
user = "…"      # identifiant Basic (clé API)
password = "…"  # secret
base_url = "https://app.baqio.com/api/v1"  # optionnel
```

L'app est déjà protégée par mot de passe (`src/auth.py`) : l'import Baqio n'est
accessible qu'après authentification.

## Gestion des erreurs

Une panne Baqio ne doit jamais empêcher la saisie et le calcul manuels.

| Cas | Comportement |
|---|---|
| 401/403 | `st.error("Identifiants Baqio invalides")` dans l'expander |
| Réseau, timeout, 5xx | `st.warning("Baqio indisponible — saisie manuelle possible")` |
| Aucune commande pré-chargée | `st.info("Aucune commande non facturée trouvée")` |
| Recherche d'un texte tapé : 401/403, réseau | mêmes messages que ci-dessus, texte retiré de la sélection |
| Variante introuvable | ligne ignorée, listée dans l'avertissement |
| Aucune ligne bouteille/magnum dans le groupe | chargement refusé + avertissement |
| Code postal introuvable / hors France | destination inchangée + avertissement |

## Tests

- `test/baqio/test_order.py` — tests unitaires purs sur des fixtures JSON **anonymisées**
  (structure réelle, aucun vrai nom ni adresse : le dépôt est public) :
  - classement 75 cl / 1,5 l / ignoré (vrac, sans format, variante introuvable) ;
  - adresse : livraison, et repli facturation via `use_billing_address` ;
  - `split_cost` : prorata en équivalent 75 cl, somme exacte, commande unique ;
  - correspondance destination : code postal à commune unique avec un nom de ville
    différent (« Paris » → « Paris 11 », sans avertissement), plusieurs communes par
    code postal (départage par la ville, accents), code postal absent, hors France.
- `test/baqio/test_client.py` — paramètres de `recent_orders` (états, tri, aucun filtre
  texte) et de `search_orders` (mêmes paramètres + filtre texte), mapping des codes HTTP
  vers les exceptions (`requests` mocké).
- `test/test_app.py` — non-régression étendue, `BaqioClient` mocké :
  - sans secret `[baqio]` : expander absent, tests existants inchangés ;
  - avec secret : commandes pré-chargées en un seul appel, pas de nouvel appel aux
    reruns, nouvel appel sur « Recharger Baqio » ;
  - texte tapé hors liste : un résultat → sélectionné ; numéro exact parmi plusieurs →
    celui-ci sélectionné ; plusieurs sans numéro exact → ajoutés, non sélectionnés,
    message ; aucun → message ; erreur → message ; texte toujours retiré de la
    sélection ; sélection existante conservée ;
  - sélection de 2 commandes → destinataire principal → chargement → `bottle`,
    `magnum`, `destination` corrects + tableau de répartition placé avant le tarif total ;
  - modification manuelle de `bottle` après chargement → répartition masquée ;
  - Baqio indisponible → avertissement, l'app reste utilisable.
