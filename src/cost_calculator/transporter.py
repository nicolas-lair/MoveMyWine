from abc import ABC, abstractmethod

import pandas as pd

from src.cost_calculator.fixed_cost_by_expedition import FixedCostByExpeditionCalculator


class AbstractTransporter(ABC):
    costByExpeditionObject: FixedCostByExpeditionCalculator = FixedCostByExpeditionCalculator()

    @property
    def cost_by_expedition(self) -> float:
        return self.costByExpeditionObject.total_cost

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
