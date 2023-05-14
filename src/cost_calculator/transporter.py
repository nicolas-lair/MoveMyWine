from abc import ABC

import pandas as pd

from src.cost_calculator.fixed_cost_by_expedition import FixedCostByExpeditionCalculator
from src.cost_calculator.cost_by_bottle import CostByBottleCalculator
from src.cost_calculator.monthly_cost import MonthlyCostCalculator
from src.constant import N_EXPEDITION


class AbstractTransporter(ABC):
    costByExpeditionObject: FixedCostByExpeditionCalculator
    costByBottle: CostByBottleCalculator
    monthlyCost: MonthlyCostCalculator

    @property
    def cost_by_expedition(self) -> float:
        return self.costByExpeditionObject.total_cost

    @property
    def cost_by_dest_and_vol(self) -> pd.DataFrame:
        return self.costByBottle.cost_by_dest_and_volume

    def get_total_cost(self, department: str, gas_factor: float, n_client: int = None, **kwargs) -> pd.DataFrame:
        if n_client is None:
            n_client = N_EXPEDITION
        df = self.cost_by_dest_and_vol.loc[department].T.copy()
        df *= gas_factor
        df += self.cost_by_expedition
        df += self.monthlyCost.get_total_cost(n_expedition_by_month=n_client)
        return df
