from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime

import pandas as pd
import streamlit as st

from src.baqio.client import (
    DEFAULT_BASE_URL,
    BaqioAuthError,
    BaqioClient,
    BaqioUnavailableError,
)
from src.baqio.destination import match_destination
from src.baqio.order import (
    BaqioOrder,
    order_label,
    parse_order,
    split_cost,
    variant_ids,
)

MAX_BOTTLES = 1200
MAX_MAGNUMS = 100
ALLOWED_STATES = ("pending", "validated")
CATALOG_TIMEOUT = 10  # seconds a load waits for the background catalogue

_catalog_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="baqio")

EXPANDER_LABEL = "📦 Importer depuis Baqio"
MSG_AUTH = "Identifiants Baqio invalides."
MSG_UNAVAILABLE = "Baqio indisponible — saisie manuelle possible."
MSG_NO_RESULT = "Aucune commande non facturée trouvée."
MSG_SEARCH_NO_RESULT = "Aucune commande non facturée pour « {text} »."
MSG_SEARCH_CHOOSE = (
    "{count} commandes trouvées pour « {text} » — ajoutées à la liste, "
    "sélectionnez-les."
)
MSG_NO_BOTTLE = "Aucune bouteille 75 cl ni magnum dans les commandes sélectionnées."
MSG_OUT_OF_RANGE = (
    "Quantités hors limites de l'app (max 1200 bouteilles, 100 magnums) "
    "— chargement annulé."
)
MSG_INVALID_ORDER = "Commande {order} illisible — ignorée."
MSG_IGNORED = "Lignes ignorées ({order}) : {lines}"
MSG_MIXED_ADDRESSES = (
    "Adresses différentes dans le groupe : destination = adresse de {customer}."
)


@dataclass(frozen=True)
class LoadedGroup:
    orders: tuple[BaqioOrder, ...]  # destinataire principal en premier
    bottles: int
    magnums: int


def baqio_enabled() -> bool:
    try:
        return "baqio" in st.secrets
    except Exception:  # noqa: BLE001 - no secrets file raises various errors
        return False


def get_client() -> BaqioClient:
    conf = st.secrets["baqio"]
    return BaqioClient(
        conf["user"],
        conf["password"],
        base_url=conf.get("base_url", DEFAULT_BASE_URL),
    )


def _add_message(level: str, text: str) -> None:
    st.session_state.baqio_messages.append((level, text))


def _valid_orders(raw_orders: list[dict]) -> list[dict]:
    kept = []
    for raw in raw_orders:
        try:
            # Client-side safety net: the API may silently ignore its state filter.
            if raw.get("state") not in ALLOWED_STATES:
                continue
            raw["id"]
            datetime.fromisoformat(raw["created_at"])
            order_label(raw)
        except (KeyError, TypeError, ValueError, AttributeError):
            _add_message(
                "warning",
                MSG_INVALID_ORDER.format(order=raw.get("name") or raw.get("id")),
            )
            continue
        kept.append(raw)
    return kept


def _refresh_orders() -> None:
    st.session_state.baqio_loaded_once = True
    st.session_state.baqio_messages = []
    try:
        client = get_client()
        raw_orders = client.recent_orders()
    except (BaqioAuthError, KeyError, TypeError):
        _add_message("error", MSG_AUTH)
        return
    except BaqioUnavailableError:
        _add_message("warning", MSG_UNAVAILABLE)
        return
    _start_catalog(client)
    raw_orders = _valid_orders(raw_orders)
    for raw in raw_orders:
        st.session_state.baqio_orders[raw["id"]] = raw
    st.session_state.baqio_results = [raw["id"] for raw in raw_orders]
    if not raw_orders:
        _add_message("info", MSG_NO_RESULT)


def _order_number(text: str) -> str:
    return text.strip().removeprefix("#").casefold()


def _search_typed(text: str) -> list[int]:
    """Search Baqio for a typed text; return the ids to select."""
    state = st.session_state
    try:
        raw_orders = get_client().search_orders(text)
    except (BaqioAuthError, KeyError, TypeError):
        _add_message("error", MSG_AUTH)
        return []
    except BaqioUnavailableError:
        _add_message("warning", MSG_UNAVAILABLE)
        return []
    found = _valid_orders(raw_orders)
    if not found:
        _add_message("info", MSG_SEARCH_NO_RESULT.format(text=text))
        return []
    for raw in found:
        state.baqio_orders[raw["id"]] = raw
        if raw["id"] not in state.baqio_results:
            state.baqio_results.append(raw["id"])
    exact = [
        raw["id"] for raw in found if _order_number(raw["name"]) == _order_number(text)
    ]
    if exact:
        return exact
    if len(found) == 1:
        return [found[0]["id"]]
    _add_message("info", MSG_SEARCH_CHOOSE.format(count=len(found), text=text))
    return []


def _resolve_typed() -> None:
    """Replace free text typed in the multiselect by the orders it finds."""
    state = st.session_state
    typed = [v for v in state.baqio_selected if isinstance(v, str)]
    if not typed:
        return
    selected = [v for v in state.baqio_selected if not isinstance(v, str)]
    for text in typed:
        if text.strip():
            selected += [i for i in _search_typed(text.strip()) if i not in selected]
    state.baqio_selected = selected


def _start_catalog(client: BaqioClient) -> None:
    """Fetch every product variant in a background thread (no Streamlit call there)."""
    st.session_state.baqio_catalog = _catalog_executor.submit(
        client.all_product_variants
    )


def _integrate_catalog() -> None:
    """Merge the background catalogue; on failure the per-id fetch takes over."""
    future = st.session_state.get("baqio_catalog")
    if future is None:
        return
    try:
        catalog = future.result(timeout=CATALOG_TIMEOUT)
    except TimeoutError:
        return  # still running: kept for the next load
    except Exception:  # noqa: BLE001 - any failure falls back to per-id fetch
        st.session_state.baqio_catalog = None
        return
    st.session_state.baqio_catalog = None
    cache = st.session_state.baqio_variants
    for variant_id, variant in catalog.items():
        cache.setdefault(variant_id, variant)


def _fetch_variants(raw_orders: list[dict]) -> None:
    _integrate_catalog()
    cache = st.session_state.baqio_variants
    client = None
    for raw in raw_orders:
        for variant_id in variant_ids(raw):
            if variant_id not in cache:
                client = client or get_client()
                cache[variant_id] = client.get_product_variant(variant_id)


def _ordered_ids() -> list[int]:
    """Selected ids, main recipient first."""
    selected = list(st.session_state.baqio_selected)
    main = st.session_state.get("baqio_main")
    if main in selected:
        selected.remove(main)
        selected.insert(0, main)
    return selected


def _load_selection(df_postal_code: pd.DataFrame) -> None:
    """Fill the form from the selected group; any refusal leaves no loaded group."""
    st.session_state.baqio_messages = []
    st.session_state.baqio_group = None
    ids = _ordered_ids()
    if not ids:
        return
    raw_orders = [st.session_state.baqio_orders[i] for i in ids]
    for raw in raw_orders:
        try:
            variant_ids(raw)
            if any(
                float(line["quantity"] or 0) < 0
                for line in raw["order_lines_not_deleted"]
            ):
                _add_message("warning", MSG_OUT_OF_RANGE)
                return
        except (KeyError, TypeError, ValueError):
            _add_message(
                "warning",
                MSG_INVALID_ORDER.format(order=raw.get("name") or raw.get("id")),
            )
            return
    try:
        _fetch_variants(raw_orders)
    except (BaqioAuthError, KeyError, TypeError):
        _add_message("error", MSG_AUTH)
        return
    except BaqioUnavailableError:
        _add_message("warning", MSG_UNAVAILABLE)
        return

    variants = st.session_state.baqio_variants
    parsed = []
    for raw in raw_orders:
        try:
            parsed.append(parse_order(raw, variants))
        except (KeyError, TypeError, ValueError):
            _add_message(
                "warning",
                MSG_INVALID_ORDER.format(order=raw.get("name") or raw.get("id")),
            )
            return
    orders = tuple(parsed)
    bottles = sum(o.bottles for o in orders)
    magnums = sum(o.magnums for o in orders)
    if sum(o.bottle_equivalent for o in orders) == 0:
        _add_message("warning", MSG_NO_BOTTLE)
        return
    if not (0 <= bottles <= MAX_BOTTLES and 0 <= magnums <= MAX_MAGNUMS):
        _add_message("warning", MSG_OUT_OF_RANGE)
        return

    main = orders[0]
    st.session_state.bottle = bottles
    st.session_state.magnum = magnums
    st.session_state.baqio_group = LoadedGroup(orders, bottles, magnums)

    for order in orders:
        if order.ignored_lines:
            lines = ", ".join(
                f"{line.description} × {line.quantity:g}"
                for line in order.ignored_lines
            )
            _add_message("warning", MSG_IGNORED.format(order=order.name, lines=lines))

    if len(df_postal_code) != 0:
        match = match_destination(df_postal_code, main.zip, main.city, main.country)
        if match.key is not None:
            st.session_state.destination = match.key
        if match.warning:
            _add_message("warning", match.warning)
    if len({(o.zip, o.city) for o in orders}) > 1:
        _add_message(
            "info", MSG_MIXED_ADDRESSES.format(customer=main.customer or main.name)
        )


def _on_selection_change(df_postal_code: pd.DataFrame) -> None:
    st.session_state.baqio_messages = []
    _resolve_typed()
    search_messages = st.session_state.baqio_messages
    _load_selection(df_postal_code)
    st.session_state.baqio_messages[:0] = search_messages


def _created_at(order_id: int) -> datetime:
    return datetime.fromisoformat(st.session_state.baqio_orders[order_id]["created_at"])


def baqio_import(df_postal_code: pd.DataFrame) -> None:
    if not baqio_enabled():
        return
    state = st.session_state
    state.setdefault("baqio_orders", {})
    state.setdefault("baqio_results", [])
    state.setdefault("baqio_selected", [])
    state.setdefault("baqio_variants", {})
    state.setdefault("baqio_group", None)
    state.setdefault("baqio_messages", [])
    if not state.get("baqio_loaded_once"):
        _refresh_orders()

    known = state.baqio_orders  # captured: format_func may run outside a script run
    options = sorted(
        set(state.baqio_results) | set(state.baqio_selected),
        key=_created_at,
        reverse=True,
    )
    with st.expander(EXPANDER_LABEL):
        st.multiselect(
            "Numéro de commande ou client",
            options=options,
            placeholder="Tapez un numéro de commande ou un client",
            key="baqio_selected",
            format_func=lambda i: order_label(known[i]) if i in known else str(i),
            accept_new_options=True,
            on_change=_on_selection_change,
            args=(df_postal_code,),
        )
        selected = list(state.baqio_selected)
        if len(selected) >= 2:
            if state.get("baqio_main") not in selected:
                state.baqio_main = selected[0]
            st.radio(
                "Destinataire principal",
                options=selected,
                key="baqio_main",
                on_change=_load_selection,
                args=(df_postal_code,),
                format_func=lambda i: (
                    (known[i].get("customer") or {}).get("name") or known[i]["name"]
                ),
            )
        st.button("Recharger Baqio", key="baqio_refresh", on_click=_refresh_orders)
        for level, text in state.baqio_messages:
            getattr(st, level)(text)


SPLIT_TITLE = "#### Répartition du groupe"
MSG_MANUAL_EDIT = "Quantités modifiées manuellement — répartition désactivée."
SPLIT_COLUMNS = ["Commande", "Client", "Éq. 75 cl", "Part (%)", "Montant HT (€)"]


def display_group_split() -> None:
    state = st.session_state
    group = state.get("baqio_group")
    if group is None or len(group.orders) < 2:
        return
    if state.get("bottle") != group.bottles or state.get("magnum") != group.magnums:
        st.info(MSG_MANUAL_EDIT)
        return
    if state.get("tarif_unavailable") or not state.get("cost"):
        return
    orders = group.orders
    total_eq = sum(o.bottle_equivalent for o in orders)
    amounts = split_cost(state.cost, orders)
    st.markdown(SPLIT_TITLE)
    st.dataframe(
        pd.DataFrame(
            [
                [
                    o.name,
                    o.customer,
                    o.bottle_equivalent,
                    round(100 * o.bottle_equivalent / total_eq, 1),
                    amount,
                ]
                for o, amount in zip(orders, amounts, strict=True)
            ],
            columns=SPLIT_COLUMNS,
        ),
        hide_index=True,
    )
