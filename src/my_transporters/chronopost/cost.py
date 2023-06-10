from pathlib import Path
from math import ceil

import pandas as pd

from src.cost_calculator import *
from src.file_structure import TarifStructureFile
from src.constant import Package, Bottle
from src.departement import DEPARTMENTS_TO_CODE
from .constant import TransporterParams

tp = TransporterParams()


class MyCostByBottleCalculator(CostByBottleCalculator):
    def __init__(self, data_folder: Path):
        self.bottle_by_package = Package.bottle_by_package
        self.extra_kg_cost = TransporterParams.extra_kg_cost

        self.tarif_structure = pd.read_csv(
            data_folder / TarifStructureFile.name,
            **TarifStructureFile.csv_format,
            index_col=[TarifStructureFile.Cols.unit]
        )

    @property
    def max_bottles(self) -> int:
        return tp.max_bottles

    def compute_weight(self, n_bottles: int, bottle_type: Bottle = Bottle()) -> float:
        n_package = ceil(n_bottles / self.bottle_by_package)
        return n_bottles * bottle_type.weight + n_package * Package.box_weight

    def get_tarif_id(self, n_bottles: int, bottle_type: Bottle = Bottle()) -> (pd.Series, float):
        weight = self.compute_weight(n_bottles=n_bottles, bottle_type=bottle_type)
        max_tarif_weight = self.tarif_structure[TarifStructureFile.Cols.max_].max()
        overweight = max(0, weight - max_tarif_weight)
        if overweight > 0:
            tarif_id = self.tarif_structure.loc[self.tarif_structure[TarifStructureFile.Cols.max_] == max_tarif_weight]
        else:
            min_weight_condition = self.tarif_structure[TarifStructureFile.Cols.min_] < weight
            max_weight_condition = self.tarif_structure[TarifStructureFile.Cols.max_] >= weight
            tarif_id = self.tarif_structure[min_weight_condition & max_weight_condition]
        return tarif_id, overweight

    def compute_cost_nationwide(self, n_bottles: int, bottle_type: Bottle = Bottle(), *args, **kwargs) -> pd.DataFrame:
        tarif_id, overweight = self.get_tarif_id(n_bottles, bottle_type=bottle_type)
        base_cost = tarif_id[TarifStructureFile.Cols.tarif].item()
        cost = base_cost + overweight * self.extra_kg_cost

        df_cost = pd.DataFrame(index=DEPARTMENTS_TO_CODE.keys(), columns=[n_bottles], data=cost)
        return df_cost

    def compute_cost(self, bottle_type=Bottle(), *args, **kwargs):
        return self.compute_cost_by_destination_and_volume(*args, bottle_type=bottle_type, **kwargs)

    def compute_cost_by_bottle(self, department: str, bottle_type=Bottle(), *args, **kwargs):
        return self.compute_cost_by_destination_and_volume(*args, bottle_type=bottle_type, **kwargs).loc[department]

    def _get_dpt_code(self, dpt_series: pd.Series) -> pd.Series:
        return dpt_series


class ChronopostTotalCost(TotalCostCalculator):
    costs = {
        CostType.ByBottle: GasModulatedCost(MyCostByBottleCalculator(data_folder=tp.data_folder), True),
        CostType.ByPackage: GasModulatedCost(CostByPackageCalculator(), True),
        CostType.Expedition: GasModulatedCost(FixedCostByExpeditionCalculator(**tp.expedition_cost), True),
    }
