import pandas as pd

from src.cost_calculator import *

from .constant import TransporterParams

tp = TransporterParams()


class GeodisCostByBottleCalculator(CostByBottleCalculator):
    def _get_dpt_code(self, dpt_series: pd.Series) -> pd.Series:
        return dpt_series.str.slice(0, 2)

    def compute_cost_nationwide(self, n_bottles: int) -> pd.Series:
        cost = super().compute_cost_nationwide(n_bottles)
        return cost


class MyTransporter(AbstractTransporter):
    costByBottle = GeodisCostByBottleCalculator(data_folder=tp.data_folder)
    costByPackage = CostByPackageCalculator()
    costByExpeditionObject = FixedCostByExpeditionCalculator(**tp.expedition_cost)
    monthlyCost = MonthlyCostCalculator(**tp.monthly_cost)
