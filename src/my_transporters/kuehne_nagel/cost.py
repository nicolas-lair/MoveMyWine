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

from .constant import TransporterParams

tp = TransporterParams()


class KNGCostByBottleCalculator(CostByBottleCalculator):
    name: CostType = CostType.ByBottle

    def __init__(self, transporter_params: TransporterParams = tp):
        super().__init__(transporter_params)

    @staticmethod
    def _get_dpt_code(series_of_dpt: pd.Series) -> pd.Series:
        return series_of_dpt.astype(str).str.zfill(2)

    def _get_tarif_unit(
        self, expedition: Union[SingleRefExpedition, MultiRefExpedition]
    ) -> tuple[UnitType, int]:
        """
        Get the tarif unit type from the number of bottles in the expedition
        :param expedition: Single ref or Multi ref expedition
        :return: tarif unit and number of corresponding units (bottle or palet)
        """
        return UnitType.BOTTLE, expedition.n_bottles_equivalent


# TODO Add cost by destination
KNGCostCollection = BaseCostList(
    [
        KNGCostByBottleCalculator(),
        FixedCostByExpe(position_cost=tp.position_cost),
        FixedCostByExpe(name=CostType.Security, security_cost=tp.security_cost),
    ]
)

KNGCostModulator = ModCostCollection(
    [
        ModulatedCostCalculator(
            name=CostType.GNRMod,
            modulated_cost=[CostType.ByBottle, CostType.Expedition],
            modulator_arg_name=tp.modulators["GNR"].arg_name,
            modulator_retriever=ModulatorFromIndicator(
                tp.data_folder / tp.modulators["GNR"].modulation_file
            ),
        ),
    ]
)

KNGTotalCost = TotalCostCalculator(
    cost_collection=KNGCostCollection,
    cost_modulator=KNGCostModulator,
)

if __name__ == "__main__":
    from src.constant import BOTTLE, MAGNUM, Package

    cost_calculator = KNGCostCollection()
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
