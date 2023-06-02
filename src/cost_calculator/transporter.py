from abc import ABC

import pandas as pd

from .fixed_cost_by_expedition import FixedCostByExpeditionCalculator
from .cost_by_bottle import CostByBottleCalculator
from .monthly_cost import MonthlyCostCalculator
from .cost_by_package import CostByPackageCalculator
from src.constant import N_EXPEDITION


class AbstractTransporter(ABC):
    costByExpeditionObject: FixedCostByExpeditionCalculator
    costByBottle: CostByBottleCalculator
    costByPackage: CostByPackageCalculator
    monthlyCost: MonthlyCostCalculator

    def __init__(self, *args, **kwargs):
        """ For cooperative multiple inheritance """
        super().__init__(*args, **kwargs)
        pass

    @property
    def cost_by_expedition(self) -> float:
        return self.costByExpeditionObject.total_cost

    def get_cost_by_bottle(self, n_bottles) -> pd.DataFrame:
        return self.costByBottle.compute_cost(n_bottles)

    def get_cost_by_package(self, n_bottles) -> pd.DataFrame:
        return self.costByPackage.compute_cost(n_bottles)

    def get_total_cost(self, n_bottles, department: str, gas_factor: float, n_client: int = None,
                       **kwargs) -> pd.DataFrame:
        if n_client is None:
            n_client = N_EXPEDITION
        df = self.get_cost_by_bottle(n_bottles).loc[department].T.copy()
        df *= gas_factor
        df += self.get_cost_by_package(n_bottles)
        df += self.cost_by_expedition
        df += self.monthlyCost.get_total_cost(n_expedition_by_month=n_client)
        return df
