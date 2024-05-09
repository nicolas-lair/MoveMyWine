import pandas as pd

from src.cost_calculator import (
    BaseCost,
    SingleRefExpedition,
    MultiRefExpedition,
    CostType,
    CostCollectionCalculator,
    CostByPackageCalculator,
    FixedCostByExpe,
)
from src.file_structure import TarifStructureFile
from src.departement import DEPARTMENTS_TO_CODE
from src.my_transporters.chronopost.constant import TransporterParams

tp = TransporterParams()


class MyCostByBottleCalculator(BaseCost):
    def __init__(self):
        super().__init__(gas_modulated=True)
        self.extra_kg_cost = tp.extra_kg_cost

        self.tarif_structure = pd.read_csv(
            tp.data_folder / TarifStructureFile.name,
            **TarifStructureFile.csv_format,
            index_col=[TarifStructureFile.Cols.unit],
        )

    @property
    def max_tarif_weight(self):
        return self.tarif_structure[TarifStructureFile.Cols.max_].max()

    def get_base_cost(self, expedition_weight: float, overweight: float) -> float:
        if overweight > 0:
            tarif_id = self.tarif_structure.loc[
                self.tarif_structure[TarifStructureFile.Cols.max_]
                == self.max_tarif_weight
            ]
        else:
            min_weight_condition = (
                self.tarif_structure[TarifStructureFile.Cols.min_] < expedition_weight
            )
            max_weight_condition = (
                self.tarif_structure[TarifStructureFile.Cols.max_] >= expedition_weight
            )
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
        df_cost = pd.DataFrame(
            index=DEPARTMENTS_TO_CODE.keys(),
            columns=[expedition.n_bottles_equivalent],
            data=cost,
        )
        return df_cost

    def compute_cost(
        self, expedition: MultiRefExpedition, department: str, *args, **kwargs
    ):
        return self.compute_cost_nationwide(expedition).loc[department]

    @staticmethod
    def _get_dpt_code(series_of_dpt: pd.Series) -> pd.Series:
        return series_of_dpt


class ChronopostCostCollection(CostCollectionCalculator):
    def __init__(self):
        super().__init__(
            {
                CostType.ByBottle: MyCostByBottleCalculator(),
                CostType.ByPackage: CostByPackageCalculator(
                    extra_package_costs=tp.extra_package_cost
                ),
                CostType.Expedition: FixedCostByExpe(**tp.fixed_cost),
            }
        )


if __name__ == "__main__":
    from src.constant import BOTTLE, Package

    cost_calculator = ChronopostCostCollection()
    expedition = MultiRefExpedition(
        [
            SingleRefExpedition(n_bottles=30, bottle_type=BOTTLE, package=Package()),
            # SingleRefExpedition(n_bottles=36, bottle_type=BOTTLE, package=Package()),
            # SingleRefExpedition(n_bottles=48, bottle_type=BOTTLE, package=Package()),
            # SingleRefExpedition(n_bottles=6, bottle_type=MAGNUM, package=Package(bottle_by_package=3))
        ]
    )
    print(
        cost_calculator.compute_cost(
            gas_factor=1 + tp.default_gas_factor / 100,
            expedition=expedition,
            department="73",
        )
    )
