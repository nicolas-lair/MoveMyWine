from .cost import StefTotalCost
from .constant import TransporterParams
from .app_custom import MyDashCustomComponent


class Stef(StefTotalCost, TransporterParams, MyDashCustomComponent):
    def __init__(self):
        super().__init__(transporter_params=TransporterParams)
