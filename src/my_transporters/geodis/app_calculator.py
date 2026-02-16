from typing import Any

import streamlit as st

from src.app_generics.transporter_app import (
    FetchedIndicator,
    TransporterApp,
    validate_transporter,
)
from src.transporter.transporter_params import ModulatorConfig

from .constant import TransporterParams
from .cost import GeodisTotalCost
from .indicator_scrapper import scrap_indicator


class GeodisApp(TransporterApp):
    cost_calculator = GeodisTotalCost
    params = TransporterParams()

    def _build_kwargs(self) -> dict[str, Any]:
        computation_kwargs = {
            self.params.modulators["GNR"].arg_name: st.session_state[
                "geodis_gnr_modulator"
            ],
            "expedition": st.session_state.expedition,
            "department": st.session_state.department,
            "postal_code": st.session_state.postal_code,
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
