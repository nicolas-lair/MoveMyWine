from abc import ABC, abstractmethod

import pandas as pd


class AbstractTransporter(ABC):
    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_total_cost(self, department: int) -> pd.DataFrame:
        pass

    def get_cost_by_bottle(self, **kwargs) -> pd.DataFrame:
        df = self.get_total_cost(**kwargs)
        df /= df.index
        return df