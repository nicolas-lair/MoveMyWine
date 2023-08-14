from typing import Final

from dash import html, dcc

from src.app_generics.dash_custom_component import DashCustomComponents
from src.app_constant import Id
from src.app_utils import build_component_id


class MyDashCustomComponent(DashCustomComponents):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _build_params_div_object(self, location: str = "", hidden: bool = True):
        params = html.Div(
            [
                html.Label([f"{self.transporter_name} : Prix du Gaz CNR, information disponible ",
                            html.A("ici", href=self.gas_modulation_link, target="_blank")]),
                html.Br(),
                dcc.Input(
                    id=Id.gas_price_input,
                    type="number",
                    min=0.981,  # TODO make params
                    max=2.3307,  # TODO make params
                    value=1.3874,
                    step=0.0001
                ),
            ],
            hidden=hidden,
            # id="-".join([location, self.transporter_name, Id.params_selector])
            id=build_component_id(location, self.transporter_name, Id.params_selector)
        )
        return params
