from .cost import MyTransporter
from .constant import TransporterParams
from src.app_generics.dash_custom_component import GasFactorParam


class Chronopost(MyTransporter, TransporterParams, GasFactorParam):
    def __init__(self):
        super().__init__(transporter_params=TransporterParams)
