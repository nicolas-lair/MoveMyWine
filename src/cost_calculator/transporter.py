from abc import ABC, abstractmethod

import pandas as pd

from src.cost_calculator.fixed_cost_by_expedition import FixedCostByExpeditionCalculator
from src.cost_calculator.gas_modulator import GasModulator
from src.cost_calculator.cost_by_bottle import CostByBottleCalculator
from src.cost_calculator.recurrent_cost import MonthlyCostCalculator


class AbstractTransporter(ABC):
    costByExpeditionObject: FixedCostByExpeditionCalculator
    gasModulator: GasModulator
    costByBottle: CostByBottleCalculator
    monthlyCost: MonthlyCostCalculator

    @property
    def cost_by_expedition(self) -> float:
        return self.costByExpeditionObject.total_cost

    @property
    def cost_by_dest_and_vol(self) -> pd.DataFrame:
        return self.costByBottle.cost_by_dest_and_volume

    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    def get_total_cost(self, department: str, gas_price: float, n_client: int = None) -> pd.DataFrame:
        df = self.cost_by_dest_and_vol.loc[department].T
        df *= self.gasModulator.get_modulation_factor(gas_price)
        df += self.cost_by_expedition
        df += self.monthlyCost.get_total_cost(n_expedition_by_month=n_client)
        return df

    def get_cost_by_bottle(self, **kwargs) -> pd.DataFrame:
        df = self.get_total_cost(**kwargs)
        df /= df.index
        return df
