from typing import Any

import streamlit as st

from src.transporter.transporter_params import ModulatorConfig
from src.app_generics.transporter_app import (
    validate_transporter,
    TransporterApp,
    FetchedIndicator,
)
from .cost import ChronopostTotalCost
from .constant import TransporterParams
from .indicator_scrapper import scrap_indicator


class ChronopostApp(TransporterApp):
    def __init__(self):
        self.cost_calculator = ChronopostTotalCost
        self.params = TransporterParams()
        st.session_state["chronopost"] = {"gnr_modulator": 100}

    def _build_kwargs(self) -> dict[str, Any]:
        computation_kwargs = {
            self.params.modulators["GNR"].arg_name: st.session_state.chronopost[
                "gnr_modulator"
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
        return self.cost_calculator.compute_cost(**kwargs)
