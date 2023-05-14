import pandas as pd
from math import ceil

from src.cost_calculator import *

from src.constant import UnitType, Package
from src.file_structure import TarifStructureFile
from .constant import TransporterParams

tp = TransporterParams()


class StefCostByBottleCalculator(CostByBottleCalculator):
    def __init__(
            self,
            max_palet_weight: int = tp.max_palet_weight,
            package_weight: int = Package.package_weight
    ):
        # TODO remove ligne Relivraison
        self.max_palet_weight = max_palet_weight
        self.package_weight = package_weight
        self.bottle_by_package = Package.bottle_by_package
        super().__init__(data_folder=tp.data_folder)

    @property
    def max_bottles_in_palet(self) -> int:
        return (self.max_palet_weight * self.bottle_by_package) // self.package_weight

    @property
    def max_bottles(self) -> int:
        max_palets = self.tarif_structure.loc[UnitType.PALET, TarifStructureFile.Cols.max_].max()
        max_bottles = max_palets * self.max_bottles_in_palet
        return max_bottles

    def _get_dpt_code(self, dpt_series: pd.Series) -> pd.Series:
        return dpt_series.str.slice(2, 4)

    def _get_price_unit(self, volume: int) -> (UnitType, int):
        max_bottles_for_bottle_price = self.tarif_structure.loc[UnitType.BOTTLE, TarifStructureFile.Cols.max_].max()
        if volume <= max_bottles_for_bottle_price:
            unit = UnitType.BOTTLE
        else:
            unit = UnitType.PALET
            volume = ceil(volume / self.max_bottles_in_palet)
        return unit, volume

    def _get_tarif_id(self, bottles: int) -> (pd.Series, int):
        unit, volume = self._get_price_unit(bottles)
        tarif_type = self.tarif_structure.loc[unit]
        tarif_id = tarif_type[
            (tarif_type[TarifStructureFile.Cols.min_] <= volume)
            & (tarif_type[TarifStructureFile.Cols.max_] >= volume)
            ]
        return tarif_id, volume


class MyTransporter(AbstractTransporter):
    def __init__(self):
        self.gasModulator = GasModulatorFromPrice(data_folder=tp.data_folder)
        self.costByBottle = StefCostByBottleCalculator()
        self.costByExpeditionObject = FixedCostByExpeditionCalculator(**tp.expedition_cost)
        self.monthlyCost = MonthlyCostCalculator()

    def get_total_cost(self, department: str, gas_price: float, n_client: int = None, **kwargs) -> pd.DataFrame:
        gas_factor = self.gasModulator.get_modulation_factor(gas_price)
        return super().get_total_cost(department, gas_factor, n_client)
