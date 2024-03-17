import streamlit as st
import sys
from pathlib import Path

sys.path.append(Path(__file__).parents[1].as_posix())

from my_transporters.stef.cost import StefTotalCost  # noqa: E402
from cost_calculator.expedition import SingleRefExpedition, MultiRefExpedition  # noqa: E402
from constant import BOTTLE, MAGNUM, Package  # noqa: E402
from departement import DEPARTMENTS_TO_CODE  # noqa: E402
from my_transporters.stef.gas_modulation_indicator import retrieve_indicator  # noqa: E402
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
    st.session_state.department = postal_code[0][:2]


df_postal_code = retrieve_postal_code()

st.markdown("#### Expédition")

if transporter == "Stef":
    from my_transporters.stef.constant import TransporterParams

    success_retrival, valid_date, current_gnr_indicator = retrieve_indicator()
    cost_calculator = StefTotalCost()

    (
        commune_col,
        dept_col,
    ) = st.columns([0.7, 0.3])
    with commune_col:
        postal_code = st.selectbox(
            "Destination",
            options=set(map(tuple, df_postal_code.values)),
            format_func=lambda c: " - ".join(c),
            on_change=department_callback,
        )
    with dept_col:
        # TODO : Update department
        st.text_input(
            "Département",
            value=DEPARTMENTS_TO_CODE[postal_code[0][:2]],
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
            if not success_retrival:
                st.error("Indicateur GNR non récupéré ! :disappointed:")
            elif not valid_date:
                st.warning("Indicateur GNR à vérifier ! :neutral_face:")
            else:
                st.success("Indicateur GNR récupéré !", icon="✅")
        with col1:
            gas_modulation = st.number_input(
                "Indice Coût GNR - [Source](%s)"
                % TransporterParams.gas_modulation_link,
                min_value=1.0,
                max_value=2.0,
                value=current_gnr_indicator,
                format="%.4f",
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
    detail_cost = cost_calculator.compute_cost(
        gas_price=gas_modulation,
        expedition=expedition,
        department=st.session_state.department,
        return_details=True,
    )
    st.session_state.cost = cost_calculator.compute_cost(
        gas_price=gas_modulation,
        expedition=expedition,
        department=st.session_state.department,
        return_details=False,
    )
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
