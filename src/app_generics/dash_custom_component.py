from typing import Final
from abc import ABC, abstractmethod

from dash import Output, Input, html, dcc

from src.app_constant import Id
from src.app_utils import build_component_id


class DashCustomComponents(ABC):
    transporter_name: str

    def __init__(self, *args, **kwargs):
        """ For cooperative multiple inheritance """
        super().__init__(*args, **kwargs)

    def build_params_selector_object(self, app, location, hidden):
        div_object = self._build_params_div_object(location, hidden)
        callback = self._build_params_selector_callback(app, location)
        return div_object, callback

    @abstractmethod
    def _build_params_div_object(self, location: str = "", hidden: bool = True):
        pass

    def _build_params_selector_callback(self, app, location: str = ""):
        @app.callback(
            Output("-".join([location, self.transporter_name, Id.params_selector]), 'hidden'),
            Input(Id.transporter_dropdown, 'value')
        )
        def update_params_selector(transporter):
            return False if transporter == self.transporter_name else True

        return update_params_selector


class GasFactorParam(DashCustomComponents):
    """
    Gas Factor Input for transporter when gas factor is available in an external web source.
    Ex : Geodis, Chronopost
    """

    def __init__(self, transporter_params, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transporter_name: Final[str] = transporter_params.name
        self.gas_modulation_link = transporter_params.gas_modulation_link
        self.default_gas_factor = transporter_params.default_gas_factor

    def _build_params_div_object(self, location: str = "", hidden: bool = True):
        params = html.Div(
            [
                html.Label(["Surcharge carburant, information disponible ",
                            html.A("ici", href=self.gas_modulation_link, target="_blank")]),
                html.Br(),
                dcc.Input(
                    id=Id.gas_factor_input,
                    type="number",
                    min=0,
                    max=100,
                    value=self.default_gas_factor,
                    step=0.5
                ),
            ],
            hidden=hidden,
            id=build_component_id(location, self.transporter_name, Id.params_selector)
        )
        return params
