import pandas as pd
from math import ceil

from src.cost_calculator import *

from src.constant import UnitType, Package, Bottle
from src.file_structure import TarifStructureFile
from .constant import TransporterParams

tp = TransporterParams()


class StefCostByBottleCalculator(CostByBottleCalculator):
    def __init__(
            self,
            max_palet_weight: int = tp.max_palet_weight,
    ):
        # TODO remove ligne Relivraison
        self.max_palet_weight = max_palet_weight
        super().__init__(data_folder=tp.data_folder)

    def get_max_bottles_in_palet(self, bottle_type: Bottle = Bottle()) -> int:
        package_weight = Package().get_package_weight(bottle=bottle_type)
        return ceil((self.max_palet_weight * Package.bottle_by_package) // package_weight)

    @property
    def max_bottles(self) -> int:
        max_palets = self.tarif_structure.loc[UnitType.PALET, TarifStructureFile.Cols.max_].max()
        max_bottles = max_palets * self.get_max_bottles_in_palet()
        return max_bottles

    def _get_dpt_code(self, dpt_series: pd.Series) -> pd.Series:
        return dpt_series.str.slice(2, 4)

    def _get_price_unit(self, volume: int) -> (UnitType, int):
        max_bottles_for_bottle_price = self.tarif_structure.loc[UnitType.BOTTLE, TarifStructureFile.Cols.max_].max()
        if volume <= max_bottles_for_bottle_price:
            unit = UnitType.BOTTLE
        else:
            unit = UnitType.PALET
            volume = ceil(volume / self.get_max_bottles_in_palet())
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
    gasModulator = GasModulatorFromPrice(data_folder=tp.data_folder)
    costByBottle = StefCostByBottleCalculator()
    costByExpeditionObject = FixedCostByExpeditionCalculator(**tp.expedition_cost)
    monthlyCost = MonthlyCostCalculator()

    def get_total_cost(self, department: str, gas_price: float, n_client: int = None, **kwargs) -> pd.DataFrame:
        gas_factor = self.gasModulator.get_modulation_factor(gas_price)
        return super().get_total_cost(department, gas_factor, n_client)
