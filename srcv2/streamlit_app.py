import streamlit as st
import sys
from pathlib import Path
from loguru import logger

logger.info(Path(__file__).parents[1].as_posix())
sys.path.append(Path(__file__).parents[1].as_posix())
logger.info(sys.path)

from my_transporters.stef.cost import StefTotalCost  # noqa: E402
from cost_calculator.expedition import SingleRefExpedition, MultiRefExpedition  # noqa: E402
from constant import BOTTLE, MAGNUM, Package  # noqa: E402
from departement import DEPARTMENTS_TO_CODE  # noqa: E402
from my_transporters.stef.gas_modulation_indicator import retrieve_indicator  # noqa: E402

transporter = st.selectbox("Choix du transporteur", ["Stef"])

if transporter == "Stef":
    from my_transporters.stef.constant import TransporterParams

    cost_calculator = StefTotalCost()

    (
        col1,
        col2,
        col3,
    ) = st.columns([0.3, 0.3, 0.4])
    with col1:
        bottle = st.number_input(
            "Nombre de bouteilles (75 cL)",
            min_value=0,
            max_value=100,
            value="min",
            step=1,
        )
        magnums = st.number_input(
            "Nombre de magnums (1.5 L)", min_value=0, max_value=100, value="min", step=1
        )
    with col2:
        destination = st.selectbox(
            "Département",
            options=DEPARTMENTS_TO_CODE.keys(),
            format_func=lambda c: DEPARTMENTS_TO_CODE[c],
        )
    with col3:
        success_retrival, valid_date, current_gnr_indicator = retrieve_indicator()
        gas_modulation = st.number_input(
            "Indice Coût GNR",
            min_value=1.0,
            max_value=2.0,
            value=current_gnr_indicator,
            format="%.4f",
        )
        if not success_retrival:
            st.error(
                "Indicateur GNR non récupéré [ici](%s) ! :disappointed:"
                % TransporterParams.gas_modulation_link
            )
        elif not valid_date:
            st.warning(
                "Indicateur GNR à vérifier [ici](%s) ! :neutral_face:"
                % TransporterParams.gas_modulation_link
            )
        else:
            st.success(
                "Indicateur GNR récupéré [ici](%s) ! :wink:"
                % TransporterParams.gas_modulation_link
            )

    cost_detail = st.checkbox("Détails des coûts")

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
    st.write(
        cost_calculator.compute_cost(
            gas_price=gas_modulation,
            expedition=expedition,
            department=destination,
            return_details=cost_detail,
        )
    )

else:
    st.write("Déso pas dispo")
