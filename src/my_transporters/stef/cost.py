from math import ceil
from typing import Union

import pandas as pd

from src.constant import UnitType
from src.cost_calculator import (
    BaseCostList,
    FixedCostByExpe,
    ModCostCollection,
    ModulatedCostCalculator,
    ModulatorFromIndicator,
    MultiRefExpedition,
    SingleRefExpedition,
    TotalCostCalculator,
)
from src.cost_calculator.constant import CostType
from src.cost_calculator.cost_by_bottle import CostByBottleCalculator
from src.file_structure import TarifStructureFile
from src.my_transporters.stef.constant import TransporterParams

tp = TransporterParams()


class StefCostByBottleCalculator(CostByBottleCalculator):
    name: CostType = CostType.ByBottle

    def __init__(self, transportation_params: TransporterParams = tp):
        super().__init__(transportation_params)

    @staticmethod
    def _get_dpt_code(series_of_dpt: pd.Series) -> pd.Series:
        return series_of_dpt.str.slice(2, 4)

    @property
    def max_bottles_at_bottle_tarif(self):
        return self.tarif_structure.loc[
            UnitType.BOTTLE, TarifStructureFile.Cols.max_
        ].max()

    def _get_tarif_unit(
        self, expedition: Union[SingleRefExpedition, MultiRefExpedition]
    ) -> tuple[UnitType, int]:
        """
        Get the tarif unit type from the number of bottles in the expedition
        :param expedition: Single ref or Multi ref expedition
        :return: tarif unit and number of corresponding units (bottle or palet)
        """
        if expedition.n_bottles_equivalent <= self.max_bottles_at_bottle_tarif:
            return UnitType.BOTTLE, expedition.n_bottles_equivalent
        else:
            n_palet = ceil(expedition.weight / tp.max_palet_weight)
            return UnitType.PALET, n_palet


StefCostCollection = BaseCostList(
    [
        StefCostByBottleCalculator(),
        FixedCostByExpe(position_cost=tp.position_cost),
        FixedCostByExpe(name=CostType.Security, security_cost=tp.security_cost),
    ]
)

StefCostModulator = ModCostCollection(
    [
        ModulatedCostCalculator(
            name=CostType.GNRMod,
            modulated_cost=[CostType.ByBottle, CostType.Expedition],
            modulator_arg_name=tp.modulators["GNR"].arg_name,
            modulator_retriever=ModulatorFromIndicator(
                tp.data_folder / tp.modulators["GNR"].modulation_file
            ),
        ),
        ModulatedCostCalculator(
            name=CostType.ColdMod,
            modulated_cost=[CostType.ByBottle, CostType.Expedition],
            modulator_arg_name=tp.modulators["Froid"].arg_name,
            modulator_retriever=ModulatorFromIndicator(
                tp.data_folder / tp.modulators["Froid"].modulation_file
            ),
        ),
    ]
)

StefTotalCost = TotalCostCalculator(
    cost_collection=StefCostCollection,
    cost_modulator=StefCostModulator,
)

if __name__ == "__main__":
    from src.constant import BOTTLE, MAGNUM, Package

    cost_calculator = StefCostCollection()
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
