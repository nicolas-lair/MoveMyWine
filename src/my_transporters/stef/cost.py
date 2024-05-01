from typing import Union

import pandas as pd

from src.cost_calculator import (
    AbstractCost,
    SingleRefExpedition,
    MultiRefExpedition,
    TotalCostCalculator,
    FixedCostByExpe,
    GasModulatorFromPrice,
)
from src.constant import UnitType, TarifType
from src.file_structure import TarifStructureFile, TarifDeptFile
from src.cost_calculator.constant import CostType
from src.my_transporters.stef.constant import TransporterParams

tp = TransporterParams()


class StefCostByBottleCalculator(AbstractCost):
    def __init__(self):
        super().__init__(gas_modulated=True)
        self.tarif_structure = pd.read_csv(
            tp.data_folder / TarifStructureFile.name,
            **TarifStructureFile.csv_format,
            index_col=[TarifStructureFile.Cols.unit],
        )
        self.tarif_by_dep = pd.read_csv(
            tp.data_folder / TarifDeptFile.name,
            **TarifDeptFile.csv_format,
            index_col=[TarifDeptFile.Cols.dpt],
        )

    @staticmethod
    def _get_dpt_code(series_of_dpt: pd.Series) -> pd.Series:
        return series_of_dpt.str.slice(2, 4)

    @property
    def max_bottles_at_bottle_tarif(self):
        return self.tarif_structure.loc[
            UnitType.BOTTLE, TarifStructureFile.Cols.max_
        ].max()

    def _get_tarif_unit(self, bottles: int) -> UnitType:
        """
        Get the tarif unit type from the number of bottles in the expedition
        :param bottles: Number of bottles in an expedition
        :return: bottle, palet or kg
        """
        if bottles <= self.max_bottles_at_bottle_tarif:
            return UnitType.BOTTLE
        else:
            raise NotImplementedError

    def _get_tarif_info(self, bottles: int, tarif_unit: UnitType) -> pd.DataFrame:
        tarif_structure = self.tarif_structure.loc[tarif_unit]
        min_volume_condition = tarif_structure[TarifStructureFile.Cols.min_] <= bottles
        max_volume_condition = tarif_structure[TarifStructureFile.Cols.max_] >= bottles
        return tarif_structure[min_volume_condition & max_volume_condition]

    def get_tarif_conditions(self, n_bottles: int) -> tuple[UnitType, TarifType, str]:
        tarif_unit = self._get_tarif_unit(n_bottles)
        assert tarif_unit == UnitType.BOTTLE
        tarif_info = self._get_tarif_info(n_bottles, tarif_unit)
        tarif_type, tarif_id = tarif_info.loc[
            tarif_unit,
            [TarifStructureFile.Cols.type_, TarifStructureFile.Cols.tarif_id],
        ]
        return tarif_unit, tarif_type, tarif_id

    def _compute_cost_nationwide(
        self, expedition: Union[SingleRefExpedition, MultiRefExpedition]
    ) -> pd.DataFrame:
        n_bottles_eq = expedition.n_bottles_equivalent
        tarif_unit, tarif_type, tarif_id = self.get_tarif_conditions(
            n_bottles=n_bottles_eq
        )
        cost = self.tarif_by_dep[tarif_id].to_frame(n_bottles_eq)
        if tarif_type == TarifType.VARIABLE:
            volume_in_tarif_unit = n_bottles_eq
            cost *= volume_in_tarif_unit
        return cost

    def _compute_cost(
        self, expedition: MultiRefExpedition, department: str, *args, **kwargs
    ) -> float:
        nation_wide_cost = self._compute_cost_nationwide(expedition)
        nation_wide_cost.index = self._get_dpt_code(nation_wide_cost.index)
        return nation_wide_cost.loc[department, expedition.n_bottles_equivalent].copy()


class StefTotalCost(TotalCostCalculator):
    def __init__(self):
        super().__init__(
            {
                CostType.ByBottle: StefCostByBottleCalculator(),
                CostType.Expedition: FixedCostByExpe(
                    position_cost=tp.position_cost, gas_modulated=True
                ),
                CostType.Security: FixedCostByExpe(
                    security_cost=tp.security_cost, gas_modulated=False
                ),
            }
        )
        self.gasModulator = GasModulatorFromPrice(data_folder=tp.data_folder)

    def compute_cost(self, gas_price: float, *args, **kwargs) -> float:
        gas_factor = self.gasModulator.get_modulation_factor(gas_price)
        return super().compute_cost(gas_factor=gas_factor, *args, **kwargs)


if __name__ == "__main__":
    from src.constant import BOTTLE, Package, MAGNUM

    cost_calculator = StefTotalCost()
    expedition = MultiRefExpedition(
        [
            SingleRefExpedition(n_bottles=30, bottle_type=BOTTLE, package=Package()),
            SingleRefExpedition(n_bottles=24, bottle_type=MAGNUM, package=Package()),
            # SingleRefExpedition(n_bottles=24, bottle_type=BOTTLE, package=Package()),
            # SingleRefExpedition(n_bottles=12, bottle_type=BOTTLE, package=Package()),
            # SingleRefExpedition(n_bottles=6, bottle_type=MAGNUM, package=Package(bottle_by_package=3))
        ]
    )
    print(
        cost_calculator.compute_cost(
            gas_price=1, expedition=expedition, department="69", return_details=True
        )
    )
