from typing import Any

import streamlit as st

from src.app_generics.scrap_cnr_indicator import scrap_indicator
from src.app_generics.transporter_app import (
    FetchedIndicator,
    TransporterApp,
    validate_transporter,
)
from src.transporter import ModulatorConfig

from .cost import StefTotalCost, TransporterParams


class StefApp(TransporterApp):
    cost_calculator = StefTotalCost
    params = TransporterParams()

    def _build_kwargs(self) -> dict[str, Any]:
        computation_kwargs = {
            self.params.modulators["GNR"].arg_name: st.session_state[
                "stef_gnr_modulator"
            ],
            self.params.modulators["Froid"].arg_name: st.session_state[
                "stef_froid_modulator"
            ],
            "expedition": st.session_state.expedition,
            "department": st.session_state.department,
            "agg": False,
        }
        return computation_kwargs

    @staticmethod
    @st.cache_data
    def scrap_indicator(modconfig: ModulatorConfig) -> FetchedIndicator:
        ind = scrap_indicator(url=modconfig.modulation_link)
        if not ind.retrieved:
            ind.value = modconfig.default
        return ind

    @validate_transporter
    def compute_cost(self) -> float:
        kwargs = self._build_kwargs()
        cost = self.cost_calculator.compute_cost(**kwargs)
        return cost
