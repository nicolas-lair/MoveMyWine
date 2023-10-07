from pathlib import Path

import pandas as pd

from srcv2.cost_calculator import *
from srcv2.file_structure import TarifStructureFile
from srcv2.departement import DEPARTMENTS_TO_CODE
from srcv2.my_transporters.chronopost.constant import TransporterParams

tp = TransporterParams()


class MyCostByBottleCalculator(AbstractCost):
    def __init__(self, data_folder: Path):
        super().__init__(gas_modulated=True)
        self.extra_kg_cost = TransporterParams.extra_kg_cost

        self.tarif_structure = pd.read_csv(
            data_folder / TarifStructureFile.name,
            **TarifStructureFile.csv_format,
            index_col=[TarifStructureFile.Cols.unit]
        )

    @property
    def max_tarif_weight(self):
        return self.tarif_structure[TarifStructureFile.Cols.max_].max()

    def get_base_cost(self, expedition_weight: float, overweight: float) -> float:
        if overweight > 0:
            tarif_id = self.tarif_structure.loc[self.tarif_structure[TarifStructureFile.Cols.max_] == self.max_tarif_weight]
        else:
            min_weight_condition = self.tarif_structure[TarifStructureFile.Cols.min_] < expedition_weight
            max_weight_condition = self.tarif_structure[TarifStructureFile.Cols.max_] >= expedition_weight
            tarif_id = self.tarif_structure[min_weight_condition & max_weight_condition]
        base_cost = tarif_id[TarifStructureFile.Cols.tarif].item()
        return base_cost

    def get_tarif_overweight(self, expedition_weight: float) -> float:
        overweight = max(0, expedition_weight - self.max_tarif_weight)
        return overweight

    def compute_cost_nationwide(self, expedition: MultiRefExpedition) -> pd.DataFrame:
        expedition_weight = expedition.weight
        overweight = self.get_tarif_overweight(expedition_weight)
        base_cost = self.get_base_cost(expedition_weight, overweight)
        cost = base_cost + overweight * self.extra_kg_cost
        df_cost = pd.DataFrame(index=DEPARTMENTS_TO_CODE.keys(), columns=[expedition.n_bottles_equivalent], data=cost)
        return df_cost

    def _compute_cost(self, expedition: MultiRefExpedition, *args, **kwargs):
        return self.compute_cost_nationwide(expedition)

    @staticmethod
    def _get_dpt_code(series_of_dpt: pd.Series) -> pd.Series:
        return series_of_dpt


class ChronopostTotalCost(TotalCostCalculator):
    def __init__(self):
        super().__init__({
            CostType.ByBottle: MyCostByBottleCalculator(data_folder=tp.data_folder),
            CostType.ByPackage: CostByPackageCalculator(gas_modulated=True),
        }
    )


if __name__ == "__main__":
    cost_calculator = ChronopostTotalCost()
    expedition = MultiRefExpedition([
        SingleRefExpedition(n_bottles=12)
    ])
    print(cost_calculator.compute_cost(gas_factor=tp.default_gas_factor, expedition=expedition))