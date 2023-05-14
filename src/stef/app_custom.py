from typing import Final

from dash import html, dcc
from .constant import TransporterParams
from src.app_generics.dash_custom_component import DashCustomComponents
from src.app_constant import Id


class MyDashCustomComponent(DashCustomComponents):
    transporter_name: Final[str] = TransporterParams.name

    def _build_params_div_object(self, location: str = "", hidden: bool = True):
        params = html.Div(
            [
                html.Label(["Prix du Gaz CNR, information disponible ",
                            html.A("ici", href=TransporterParams.gas_modulation_link, target="_blank")]),
                html.Br(),
                dcc.Input(
                    id=Id.gas_price_input,
                    type="number",
                    min=0.981,  # TODO make params
                    max=2.3307,  # TODO make params
                    value=1.409,
                    step=0.05
                ),
            ],
            hidden=hidden,
            id="-".join([location, self.transporter_name, Id.params_selector])
        )
        return params
