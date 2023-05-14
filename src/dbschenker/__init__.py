from .cost import MyTransporter
from .constant import TransporterParams
from .app_custom import MyDashCustomComponent


class DBSchenker(MyTransporter, TransporterParams, MyDashCustomComponent):
    pass
