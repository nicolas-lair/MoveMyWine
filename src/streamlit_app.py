import sys
from pathlib import Path
from dataclasses import asdict

from urllib.error import URLError
import pandas as pd
import streamlit as st

sys.path.append(Path(__file__).parents[1].as_posix())

from src.streamlit_utils import (  # noqa: E402
    define_style,
    bottle_input,
    retrieve_postal_code,
    destination_city_input,
    input_factor,
    init_session_state,
    display_result,
    cost_callback,
    TRANSPORTER_LIST,
    store_init_date,
    clear_cache_on_new_month,
)

st.title(":champagne: Move My Wine")

store_init_date()
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
    init_session_state("postal_code", df_postal_code.loc[0, "full_name"])
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
