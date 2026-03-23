from datetime import date
from typing import Any

import pandas as pd
import streamlit as st

from src.app_generics.postal_code import PostalCodeAPI, get_postal_code_df
from src.constant import BOTTLE, MAGNUM, Package
from src.cost_calculator import MultiRefExpedition, SingleRefExpedition
from src.departement import DEPARTMENTS_TO_CODE
from src.my_transporters import ChronopostApp, StefApp
from src.my_transporters.geodis import GeodisApp

TRANSPORTER_LIST = [
    StefApp(),
    GeodisApp(),
    ChronopostApp(),
    # KNGApp(),
]


def init_session_state(var_name: str, init_value: Any = None):
    if st.session_state.get(var_name) is None:
        st.session_state[var_name] = init_value


@st.cache_data
def retrieve_postal_code():
    return get_postal_code_df()


def clear_cache_on_new_month():
    init_session_state("init_date", date.today())
    if date.today().month != st.session_state["init_date"].month:
        st.cache_data.clear()
        st.session_state["init_date"] = date.today()


@st.fragment
def define_style():
    st.markdown(
        """
    <style>
    .mid-font {
        font-size:25px;
        text-align: center
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <style>
    .big-font {
        font-size:50px !important;
        text-align: center
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def build_expedition():
    st.session_state.expedition = MultiRefExpedition(
        [
            SingleRefExpedition(
                n_bottles=st.session_state.bottle, bottle_type=BOTTLE, package=Package()
            ),
            SingleRefExpedition(
                n_bottles=st.session_state.magnum, bottle_type=MAGNUM, package=Package()
            ),
        ]
    )


def cost_callback():
    build_expedition()
    st.session_state.detail_cost = st.session_state.transporter.compute_cost()
    st.session_state.cost = round(sum(st.session_state.detail_cost.values(), 0), 2)


def bottle_input():
    (
        col1,
        col2,
    ) = st.columns([0.25, 0.25])
    with col1:
        st.number_input(
            "Bouteilles (75 cL)",
            min_value=0,
            max_value=1200,
            value="min",
            step=6,
            key="bottle",
        )
    with col2:
        st.number_input(
            "Magnums (1.5 L)",
            min_value=0,
            max_value=100,
            value="min",
            step=3,
            key="magnum",
        )


def destination_city_input(df_postal_code):
    if len(df_postal_code) != 0:
        (
            commune_col,
            dept_col,
        ) = st.columns([0.7, 0.3])
        with commune_col:
            st.selectbox(
                "Destination",
                options=df_postal_code.index.tolist(),
                key="destination",
            )
            st.session_state["department"] = st.session_state.destination[:2]
            st.session_state["postal_code"] = df_postal_code.loc[
                st.session_state.destination, PostalCodeAPI.Cols.postal_code
            ]
        with dept_col:
            st.text_input(
                "Département",
                value=DEPARTMENTS_TO_CODE[st.session_state.department],
                disabled=True,
            )


def input_factor(
    indicator,
    name,
    modulation_link: str,
    min_value: float,
    max_value: float,
    input_format: str,
    **kwargs,
):
    col1, col2 = st.columns([0.2, 0.5])
    with col2:
        st.text("")
        if not indicator.retrieved:
            st.error(f"Indicateur {name} non récupéré ! :disappointed:")
        elif not indicator.valid_date:
            st.warning(f"Indicateur {name} à vérifier ! :neutral_face:")
        else:
            st.success(f"Indicateur {name} récupéré !", icon="✅")
    with col1:
        st.number_input(
            f"Indice Coût {name} - [Source](%s)" % modulation_link,
            min_value=min_value,
            max_value=max_value,
            value=indicator.value,
            format=input_format,
            help="Récupéré automatiquement si possible",
            key=f"{st.session_state.transporter.params.name.lower()}_{name.lower()}_modulator",
        )


def display_result(result):
    result.markdown(
        f'<p class="big-font">{st.session_state.cost} €</p>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f'<p class="big-font">{st.session_state.cost} € HT</p>',
            unsafe_allow_html=True,
        )
    with col2:
        st.write(st.session_state.detail_cost)


def display_comparison():
    if not st.session_state.get("bottle") and not st.session_state.get("magnum"):
        st.info("Renseignez le nombre de bouteilles pour comparer les transporteurs.")
        return

    st.caption(
        "Les surcharges utilisent les valeurs récupérées automatiquement pour chaque transporteur."
    )

    indicator_issues = []

    # Phase 1 : scraping et initialisation du session state
    for transporter in TRANSPORTER_LIST:
        name_lower = transporter.params.name.lower()
        for mod_name, mod in transporter.params.modulators.items():
            main_key = f"{name_lower}_{mod_name.lower()}_modulator"
            indicator = transporter.scrap_indicator(mod)
            fallback = indicator.value if indicator is not None else mod.default
            init_session_state(main_key, fallback)
            if indicator is None or not indicator.retrieved:
                indicator_issues.append(
                    (transporter.params.name, mod_name, "non récupéré")
                )
            elif not indicator.valid_date:
                indicator_issues.append(
                    (transporter.params.name, mod_name, "date à vérifier")
                )

    # Phase 2 : expander indicateurs (toujours affiché)
    n_issues = len(indicator_issues)
    expander_title = (
        f"⚠️ {n_issues} alerte{'s' if n_issues > 1 else ''} concernant les Indicateurs"
        if n_issues
        else "✅ Indicateurs OK"
    )
    with st.expander(expander_title, expanded=False):
        if not indicator_issues:
            st.success("Tous les indicateurs ont été récupérés correctement.")
        else:
            for transporter_name, mod_name, reason in indicator_issues:
                st.warning(
                    f"**{transporter_name} / {mod_name}** ({reason}) "
                    f"— valeur ajustable manuellement dans l'onglet *Tarif détaillé*"
                )

    # Phase 3 : calcul des coûts
    results = {}
    errors = []
    for transporter in TRANSPORTER_LIST:
        try:
            detail = transporter.compute_cost()
            results[transporter.params.name] = detail
        except Exception:
            errors.append(transporter.params.name)

    if errors:
        st.warning(f"Calcul impossible pour : {', '.join(errors)}")

    if not results:
        st.error("Impossible de calculer les coûts pour aucun transporteur.")
        return

    totals = {name: round(sum(detail.values()), 2) for name, detail in results.items()}

    st.markdown("#### Coût total par transporteur (HT)")
    df_totals = pd.DataFrame.from_dict(totals, orient="index", columns=["Coût HT (€)"])
    st.dataframe(df_totals.style.format("{:.2f} €"))

    with st.expander("Détail par poste de coût"):
        df_detail = pd.DataFrame(
            {
                name: {k.value: round(v, 2) for k, v in detail.items()}
                for name, detail in results.items()
            }
        ).fillna(0)
        st.dataframe(df_detail.style.format("{:.2f} €"))
