from .cost import DBSchenkerTotalCost
from .constant import TransporterParams
from .app_custom import MyDashCustomComponent


class DBSchenker(DBSchenkerTotalCost, TransporterParams, MyDashCustomComponent):
    pass
