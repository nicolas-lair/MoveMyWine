import sys
from pathlib import Path
from dataclasses import asdict

from urllib.error import URLError
import pandas as pd
import streamlit as st

sys.path.append(Path(__file__).parents[1].as_posix())

from streamlit_utils import (  # noqa: E402
    define_style,
    bottle_input,
    retrieve_postal_code,
    destination_city_input,
    input_factor,
    init_session_state,
    display_result,
    COST_CALCULATOR,
    cost_calculator_callback,
)

st.title(":champagne: Move My Wine")

define_style()

init_session_state("detail_cost", {})
init_session_state("cost", 0)

init_session_state("bottle", 0)
init_session_state("magnum", 0)

init_session_state("transporter", "Stef")
init_session_state("department", "01")
cost_calculator_callback()

col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Transporteur")
    st.selectbox(
        "Choix du transporteur",
        COST_CALCULATOR.keys(),
        label_visibility="hidden",
        key="transporter",
        on_change=cost_calculator_callback,
    )

with col2:
    st.markdown(
        '<p class="mid-font">Coût Transport (HT)</p>',
        unsafe_allow_html=True,
    )
    result = st.markdown(
        f'<p class="big-font">{st.session_state.cost} €</p>',
        unsafe_allow_html=True,
    )

try:
    df_postal_code = retrieve_postal_code()
    init_session_state("postal_code", df_postal_code.loc[0, "full_name"])
except URLError as e:
    print(e)
    df_postal_code = pd.DataFrame()

st.markdown("#### Expédition")

destination_city_input(df_postal_code)
bottle_input()

with st.expander("Surcharges", expanded=True):
    indicator_dict = {
        mod_name: st.session_state.cost_calculator.scrap_indicator(mod)
        for mod_name, mod in st.session_state.cost_calculator.params.modulators.items()
    }
    for mod_name, mod in st.session_state.cost_calculator.params.modulators.items():
        input_factor(indicator_dict[mod_name], name=mod_name, **asdict(mod))

display_result()
