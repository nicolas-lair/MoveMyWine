from typing import Final

from dash import html, dcc
from .constant import TransporterParams
from src.app_constant import Id
from src.app_generics.dash_custom_component import DashCustomComponents
from src.app_utils import build_component_id


class MyDashCustomComponent(DashCustomComponents):
    transporter_name: Final[str] = TransporterParams.name

    def _build_params_div_object(self, location: str = "", hidden: bool = True):
        params = html.Div(
            [
                html.Label(["Surcharge carburant, information disponible ",
                            html.A("ici", href=TransporterParams.gas_modulation_link, target="_blank")]),
                html.Br(),
                dcc.Input(
                    id=Id.gas_factor_input,
                    type="number",
                    min=0,  # TODO make params
                    max=100,  # TODO make params
                    value=15.57,
                    step=0.5
                ),
            ],
            hidden=hidden,
            id=build_component_id(location, self.transporter_name, Id.params_selector)
        )
        return params
