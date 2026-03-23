from typing import Union

import numpy as np
import pandas as pd

from src.constant import UnitType
from src.cost_calculator import (
    BaseCostCalculator,
    BaseCostList,
    CostType,
    FixedCostByExpe,
    ModCostCollection,
    ModulatedCostCalculator,
    MultiRefExpedition,
    SingleRefExpedition,
    TotalCostCalculator,
    round_cost,
)
from src.cost_calculator.cost_by_bottle import CostByBottleCalculator
from src.file_structure import (
    CorrespondanceZoneDpt,
    MapZone2PostalCode,
    TarifStructureFile,
    TarifZoneFile,
)
from src.my_transporters.geodis.constant import TransporterParams

tp = TransporterParams()


class MyCostByBottleCalculator(CostByBottleCalculator):
    name: CostType = CostType.ByBottle

    def __init__(self, transporter_params: TransporterParams = tp):
        self.tarif_structure = TarifStructureFile().load(
            transporter_params.data_folder,
            index_col=[TarifStructureFile.Cols.unit],
        )

        tarif_by_zone = TarifZoneFile().load(transporter_params.data_folder)
        dept_by_zone = CorrespondanceZoneDpt().load(transporter_params.data_folder)
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


class CostByDestination(BaseCostCalculator):
    name = CostType.ByDestination

    def __init__(self, transporter_params: TransporterParams = tp):
        self.zone_map = transporter_params.extra_destination_cost[
            "postalcode2zone"
        ].load(
            data_folder=transporter_params.data_folder,
            index_col=MapZone2PostalCode.Cols.destination,
        )
        self.weight_category = np.array(
            transporter_params.extra_destination_cost["weight_limit"]
        )
        self.cost_by_zone = transporter_params.extra_destination_cost["cost"]

    @staticmethod
    def _get_index_from_interval(value: int, interval_list: list[int]) -> int:
        return (value > np.array(interval_list)).sum()

    def get_weight_category(self, exp: MultiRefExpedition) -> int:
        return self._get_index_from_interval(exp.weight, self.weight_category)

    @round_cost()
    def compute_cost(
        self,
        expedition: MultiRefExpedition,
        postal_code: str,
        department: str,
        **kwargs,
    ) -> float:
        row = self.zone_map.index.intersection([postal_code, department])
        if len(row) == 0:
            return 0.0
        elif len(row) == 1:
            zone = self.zone_map.loc[row[0], MapZone2PostalCode.Cols.zone]
            weight_cat = self.get_weight_category(expedition)
            return self.cost_by_zone[zone][weight_cat]
        else:
            raise ValueError(
                f"Two corresponding rows were found in the file 'zones urbaines contraintes' for "
                f"postal_code {postal_code} and department {department}. This should not be possible."
            )


GeodisCostCollection = BaseCostList(
    [
        MyCostByBottleCalculator(),
        CostByDestination(),
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
                    CostType.Expedition,
                    CostType.ByDestination,
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
