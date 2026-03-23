import sys
from dataclasses import asdict
from pathlib import Path
from urllib.error import URLError

import pandas as pd
import streamlit as st

sys.path.append(Path(__file__).parents[1].as_posix())

from src.streamlit_utils import (  # noqa: E402
    TRANSPORTER_LIST,
    bottle_input,
    clear_cache_on_new_month,
    cost_callback,
    define_style,
    destination_city_input,
    display_result,
    init_session_state,
    input_factor,
    retrieve_postal_code,
)

st.title(":champagne: Move My Wine")

clear_cache_on_new_month()
define_style()

init_session_state("detail_cost", {})
init_session_state("cost", 0.0)

col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Transporteur")
    st.selectbox(
        "Choix du transporteur",
        TRANSPORTER_LIST,
        label_visibility="hidden",
        key="transporter",
        format_func=lambda x: x.params.name,
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
    init_session_state("destination", df_postal_code.index[0])
except URLError as e:
    print(e)
    df_postal_code = pd.DataFrame()

st.markdown("#### Expédition")

destination_city_input(df_postal_code)
bottle_input()

with st.expander("Surcharges", expanded=True):
    indicator_dict = {
        mod_name: st.session_state.transporter.scrap_indicator(mod)
        for mod_name, mod in st.session_state.transporter.params.modulators.items()
    }
    for mod_name, mod in st.session_state.transporter.params.modulators.items():
        input_factor(indicator_dict[mod_name], name=mod_name, **asdict(mod))

cost_callback()
display_result(result)
