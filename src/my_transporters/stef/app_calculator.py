from typing import Any

import streamlit as st

from src.transporter import ModulatorConfig
from src.app_generics.transporter_app import (
    TransporterApp,
    validate_transporter,
    FetchedIndicator,
)
from .cost import StefTotalCost, TransporterParams
from .indicator_scrapper import scrap_indicator


class StefApp(TransporterApp):
    def __init__(self):
        self.cost_calculator = StefTotalCost
        self.params = TransporterParams()
        st.session_state["stef"] = {"gnr_modulator": 1, "cold_modulator": 1}

    def _build_kwargs(self) -> dict[str, Any]:
        computation_kwargs = {
            self.params.modulators["GNR"].arg_name: st.session_state.stef[
                "gnr_modulator"
            ],
            self.params.modulators["Froid"].arg_name: st.session_state.stef[
                "cold_modulator"
            ],
            "expedition": st.session_state.expedition,
            "department": st.session_state.department,
            "agg": False,
        }
        return computation_kwargs

    @staticmethod
    @st.cache_data
    def scrap_indicator(modconfig: ModulatorConfig) -> FetchedIndicator:
        return scrap_indicator(url=modconfig.modulation_link)

    @validate_transporter
    def compute_cost(self) -> float:
        kwargs = self._build_kwargs()
        cost = self.cost_calculator.compute_cost(**kwargs)
        return cost
