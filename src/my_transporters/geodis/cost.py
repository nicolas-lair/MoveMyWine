from typing import Union

import pandas as pd

from src.constant import UnitType
from src.cost_calculator import (
    BaseCostList,
    CostType,
    FixedCostByExpe,
    ModCostCollection,
    ModulatedCostCalculator,
    MultiRefExpedition,
    SingleRefExpedition,
    TotalCostCalculator,
)
from src.cost_calculator.cost_by_bottle import CostByBottleCalculator
from src.file_structure import (
    CorrespondanceZoneDpt,
    TarifStructureFile,
    TarifZoneFile,
)
from src.my_transporters.geodis.constant import TransporterParams

tp = TransporterParams()


class MyCostByBottleCalculator(CostByBottleCalculator):
    name: CostType = CostType.ByBottle

    def __init__(self, transporter_params: TransporterParams = tp):
        self.tarif_structure = TarifStructureFile.load(
            transporter_params.data_folder,
            index_col=[TarifStructureFile.Cols.unit],
        )

        tarif_by_zone = TarifZoneFile.load(transporter_params.data_folder)
        dept_by_zone = CorrespondanceZoneDpt.load(transporter_params.data_folder)
        self.tarif_by_dep = (
            pd.merge(
                dept_by_zone.reset_index(),
                tarif_by_zone.reset_index(),
                on=TarifZoneFile.Cols.zone,
                how="left",  # To keep all dpt
            )
            .drop(columns=TarifZoneFile.Cols.zone)
            .set_index(CorrespondanceZoneDpt.Cols.dpt)
        )

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


# class CostByDestination(BaseCostCalculator):
#     name = CostType.ByDestination
#
#     @round_cost()
#     def compute_cost(self, expedition: MultiRefExpedition, postal_code: int, **kwargs) -> float:
#         ...

GeodisCostCollection = BaseCostList(
    [
        MyCostByBottleCalculator(),
        FixedCostByExpe(**tp.fixed_cost),
    ]
)

GeodisTotalCost = TotalCostCalculator(
    cost_collection=GeodisCostCollection,
    cost_modulator=ModCostCollection(
        [
            ModulatedCostCalculator(
                name=CostType.GNRMod,
                modulated_cost=[
                    CostType.ByBottle,
                ],
                modulator_arg_name=tp.modulators["GNR"].arg_name,
            )
        ]
    ),
)

if __name__ == "__main__":
    from src.constant import BOTTLE, Package, UnitType

    cost_calculator = GeodisCostCollection
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
            gas_factor=14.89,
            expedition=expedition,
            department="73",
        )
    )
