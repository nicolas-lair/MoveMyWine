import pandas as pd

from src.cost_calculator import *
from src.constant import Package

from .constant import TransporterParams as tp


class GeodisCostByBottleCalculator(CostByBottleCalculator):
    def _get_dpt_code(self, dpt_series: pd.Series) -> pd.Series:
        return dpt_series.str.slice(0, 2)

    @staticmethod
    def compute_multi_package_cost(
            volume: int,
            extra_cost: float = tp.extra_package_cost,
            max_free_package: int = tp.max_free_package,
            max_multi_package_fee: float = tp.multi_package_max_fee
    ) -> float:
        cost = 0
        n_package = volume // Package.bottle_by_package
        if Package.max_package_without_palet < n_package < max_free_package:
            cost = extra_cost * (n_package * max_free_package)
            cost = min(cost, max_multi_package_fee)
        return cost

    def _compute_cost(self, volume: int) -> pd.Series:
        cost = super()._compute_cost(volume)
        cost += self.compute_multi_package_cost(volume)
        return cost


class MyTransporter(AbstractTransporter):
    def __init__(self):
        self.gasModulator = GasModulator(data_folder=tp.data_folder)
        self.costByBottle = GeodisCostByBottleCalculator(data_folder=tp.data_folder)
        self.costByExpeditionObject = FixedCostByExpeditionCalculator(**tp.expedition_cost)
        self.monthlyCost = MonthlyCostCalculator(**tp.monthly_cost)
