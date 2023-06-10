from .cost import GeodisTotalCost
from .constant import TransporterParams
from src.app_generics.dash_custom_component import GasFactorParam


class Geodis(GeodisTotalCost, TransporterParams, GasFactorParam):
    def __init__(self):
        super().__init__(transporter_params=TransporterParams)
