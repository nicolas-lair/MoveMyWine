import streamlit as st
import sys
from pathlib import Path

sys.path.append(Path(__file__).parents[1].as_posix())

from my_transporters.stef.cost import StefTotalCost  # noqa: E402
from cost_calculator.expedition import SingleRefExpedition, MultiRefExpedition  # noqa: E402
from constant import BOTTLE, MAGNUM, Package  # noqa: E402
from departement import DEPARTMENTS_TO_CODE  # noqa: E402
from my_transporters.stef.indicator_scrapper import cache_indicator  # noqa: E402
from app_generics.postal_code import get_postal_code_list  # noqa: E402

st.title(":champagne: Move My Wine")
if "cost" not in st.session_state:
    st.session_state.cost = 0

col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Transporteur")
    transporter = st.selectbox(
        "Choix du transporteur", ["Stef"], label_visibility="hidden"
    )
with col2:
    st.text("")
    result = st.empty()


@st.cache_data
def retrieve_postal_code():
    return get_postal_code_list()


if "department" not in st.session_state:
    st.session_state.department = "75"


def department_callback():
    st.session_state.department = postal_code[:2]


df_postal_code = retrieve_postal_code()

st.markdown("#### Expédition")

if transporter == "Stef":
    cost_calculator = StefTotalCost
    gnr_indicator = cache_indicator(StefTotalCost.params.gnr_modulation_link)
    cold_indicator = cache_indicator(StefTotalCost.params.cold_modulation_link)

    (
        commune_col,
        dept_col,
    ) = st.columns([0.7, 0.3])
    with commune_col:
        postal_code = st.selectbox(
            "Destination",
            options=df_postal_code.full_name.values,
            on_change=department_callback,
        )
    with dept_col:
        # TODO : Update department
        st.text_input(
            "Département",
            value=DEPARTMENTS_TO_CODE[postal_code[:2]],
            disabled=True,
        )

    (
        col1,
        col2,
    ) = st.columns([0.25, 0.25])
    with col1:
        bottle = st.number_input(
            "Bouteilles (75 cL)",
            min_value=0,
            max_value=100,
            value="min",
            step=1,
        )
    with col2:
        magnums = st.number_input(
            "Magnums (1.5 L)", min_value=0, max_value=100, value="min", step=1
        )

    with st.expander("Surcharges", expanded=True):
        col1, col2 = st.columns([0.2, 0.5])
        with col2:
            st.text("")
            if not gnr_indicator.retrieved:
                st.error("Indicateur GNR non récupéré ! :disappointed:")
            elif not gnr_indicator.valid_date:
                st.warning("Indicateur GNR à vérifier ! :neutral_face:")
            else:
                st.success("Indicateur GNR récupéré !", icon="✅")
        with col1:
            gnr_modulation = st.number_input(
                "Indice Coût GNR - [Source](%s)"
                % StefTotalCost.params.gnr_modulation_link,
                min_value=1.0,
                max_value=2.0,
                value=gnr_indicator.value,
                format="%.4f",
                help="Récupéré automatiquement si possible",
            )

        col1, col2 = st.columns([0.2, 0.5])
        with col2:
            st.text("")
            if not cold_indicator.retrieved:
                st.error("Indicateur Froid non récupéré ! :disappointed:")
            elif not cold_indicator.valid_date:
                st.warning("Indicateur Froid à vérifier ! :neutral_face:")
            else:
                st.success("Indicateur Froid récupéré !", icon="✅")
        with col1:
            cold_modulation = st.number_input(
                "Indice Coût Froid - [Source](%s)"
                % StefTotalCost.params.cold_modulation_link,
                min_value=0.0,
                max_value=750.0,
                value=cold_indicator.value,
                format="%.2f",
                help="Récupéré automatiquement si possible",
            )

    expedition = MultiRefExpedition(
        [
            SingleRefExpedition(
                n_bottles=bottle, bottle_type=BOTTLE, package=Package()
            ),
            SingleRefExpedition(
                n_bottles=magnums, bottle_type=MAGNUM, package=Package()
            ),
        ]
    )

    computation_kwargs = {
        StefTotalCost.params.gnr_arg_name: gnr_modulation,
        StefTotalCost.params.cold_arg_name: cold_modulation,
        "expedition": expedition,
        "department": st.session_state.department,
        "agg": False,
    }

    detail_cost = cost_calculator.compute_cost(**computation_kwargs)
    st.session_state.cost = round(sum(detail_cost.values(), 0), 2)

    col1, col2 = st.columns(2)
    with col1:
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
        st.markdown(
            f'<p class="big-font">{st.session_state.cost} € HT</p>',
            unsafe_allow_html=True,
        )
        result.markdown(
            f'<p class="big-font">{st.session_state.cost} € HT</p>',
            unsafe_allow_html=True,
        )
    with col2:
        st.write(detail_cost)

else:
    st.write("Déso pas dispo")
