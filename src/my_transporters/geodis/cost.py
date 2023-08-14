import pandas as pd

from src.cost_calculator import *

from .constant import TransporterParams

tp = TransporterParams()


class GeodisCostByBottleCalculator(CostByBottleCalculator):
    @staticmethod
    def _get_dpt_code(dpt_series: pd.Series) -> pd.Series:
        return dpt_series.str.slice(0, 2)


class GeodisTotalCost(TotalCostCalculator):
    costs = {
        CostType.ByBottle: GasModulatedCost(GeodisCostByBottleCalculator(data_folder=tp.data_folder), True),
        CostType.ByPackage: GasModulatedCost(CostByPackageCalculator(extra_package_costs=tp.extra_package_cost), True),
        CostType.Expedition: GasModulatedCost(FixedCostByExpe(**tp.expedition_cost), True),
        CostType.Monthly: GasModulatedCost(MonthlyCostCalculator(**tp.monthly_cost), False)
    }
