from typing import Final

from dash import html, dcc
from .constant import TransporterParams
from src.app_constant import Id
from src.app_generics.dash_custom_component import DashCustomComponents
from src.app_utils import build_component_id


class MyDashCustomComponent(DashCustomComponents):
    transporter_name: Final[str] = TransporterParams.name

    def _build_params_div_object(self, location: str = "", hidden: bool = True):
        # For compatibility
        params = html.Div(
            hidden=hidden,
            id=build_component_id(location, self.transporter_name, Id.params_selector))
        return params
