from .cost import MyTransporter
from .constant import TransporterParams
from .app_custom import MyDashCustomComponent


class Stef(MyTransporter, TransporterParams, MyDashCustomComponent):
    pass
