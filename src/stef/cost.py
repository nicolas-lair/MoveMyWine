import pandas as pd

from src.cost_calculator.gas_modulator import GasModulator
from src.cost_calculator.transporter import AbstractTransporter
from src.cost_calculator.fixed_cost_by_expedition import FixedCostByExpeditionCalculator
from src.cost_calculator.cost_by_bottle import CostByBottleCalculator
from src.constant import UnitType, BOTTLE_BY_PACKAGE, PACKAGE_WEIGHT
from src.file_structure import TarifStructureFile
from src.stef.constant import TransporterParams as p


class StefCostByBottleCalculator(CostByBottleCalculator):
    def __init__(
            self,
            max_palet_weight: int = p.max_palet_weight,
            package_weight: int = PACKAGE_WEIGHT
    ):
        super().__init__(data_folder=p.data_folder)
        self.max_palet_weight = max_palet_weight
        self.package_weight = package_weight
        self.bottle_by_package = BOTTLE_BY_PACKAGE

    @property
    def max_bottles(self) -> int:
        return self.tarif_structure.loc[UnitType.BOTTLE, TarifStructureFile.Cols.max_].max()

    @property
    def max_bottles_in_palet(self) -> int:
        return (self.max_palet_weight * self.bottle_by_package) // self.package_weight


class MyTransporter(AbstractTransporter):
    def __init__(self):
        self.gasModulator = GasModulator(data_folder=p.data_folder)
        self.costByBottle = StefCostByBottleCalculator()
        self.costByExpeditionObject = FixedCostByExpeditionCalculator(**p.expedition_cost)

        max_bottles = self.costByBottle.max_bottles
        self.bottle_cost = pd.concat(
            [self.costByBottle.compute_bottle_cost_nationwide(n_bottles=i) for i in range(max_bottles + 1)],
            axis=1
        )

        self.palet_cost = pd.concat(
            [self.costByBottle.compute_palet_cost_nationwide(n_palets=i) for i in range(11)],
            axis=1
        )

    @staticmethod
    def _get_dept_code(department: str) -> str:
        return f"FR{department}"

    def get_total_cost(self, department: str, gas_price: float = 1.40) -> pd.DataFrame:
        df = self.bottle_cost.loc[self._get_dept_code(department)].T
        df *= self.gasModulator.get_modulation_factor(gas_price)
        df += self.costByExpeditionObject.total_cost
        return df

    def get_cost_by_bottle(self, department: str, gas_price: float) -> pd.DataFrame:
        return super().get_cost_by_bottle(department=department, gas_price=gas_price)
