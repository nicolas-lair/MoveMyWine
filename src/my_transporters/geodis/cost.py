import numpy as np
import pandas as pd

from src.constant import UnitType
from src.cost_calculator import (
    BaseCostCalculator,
    BaseCostList,
    CostByPaletCalculator,
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
from src.my_transporters.geodis.constant import (
    GeodisParams,
    MessagerieParams,
    PaletteParams,
)

messagerie_tp = MessagerieParams()
palette_tp = PaletteParams()


class MyCostByBottleCalculator(CostByBottleCalculator):
    """Tarif by zone, priced by bottle (messagerie)"""

    name: CostType = CostType.ByBottle

    def __init__(self, transporter_params: GeodisParams = messagerie_tp):
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
        self, expedition: SingleRefExpedition | MultiRefExpedition
    ) -> tuple[UnitType, int]:
        """
        Get the tarif unit type from the number of bottles in the expedition
        :param expedition: Single ref or Multi ref expedition
        :return: tarif unit and number of corresponding units (bottle or palet)
        """
        return UnitType.BOTTLE, expedition.n_bottles_equivalent


class MyCostByPaletCalculator(MyCostByBottleCalculator):
    """Same tarif by zone, priced by palet"""

    def __init__(self, transporter_params: PaletteParams = palette_tp):
        super().__init__(transporter_params)
        self.max_palet_weight = transporter_params.max_palet_weight
        self.palet_weight = transporter_params.palet_weight

    def _get_tarif_unit(
        self, expedition: SingleRefExpedition | MultiRefExpedition
    ) -> tuple[UnitType, int]:
        return UnitType.PALET, expedition.n_palets(
            self.max_palet_weight, self.palet_weight
        )


class CostByDestination(BaseCostCalculator):
    name = CostType.ByDestination

    def __init__(self, transporter_params: GeodisParams = messagerie_tp):
        self.zone_map = transporter_params.extra_destination_cost[
            "postalcode2zone"
        ].load(
            data_folder=transporter_params.common_data_folder,
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


def build_total_cost(
    transporter_params: GeodisParams,
    cost_by_unit: BaseCostCalculator,
    palet_cost: BaseCostCalculator,
) -> TotalCostCalculator:
    """Geodis offers only differ by their unit tarif and their palet cost"""
    return TotalCostCalculator(
        cost_collection=BaseCostList(
            [
                cost_by_unit,
                CostByDestination(transporter_params),
                FixedCostByExpe(
                    name=CostType.Security,
                    security_cost=transporter_params.surete_cost,
                ),
                palet_cost,
            ]
        ),
        cost_modulator=ModCostCollection(
            [
                ModulatedCostCalculator(
                    name=CostType.GNRMod,
                    modulated_cost=[
                        CostType.ByBottle,
                        CostType.Security,
                        CostType.ByDestination,
                    ],
                    modulator_arg_name=transporter_params.modulators["GNR"].arg_name,
                )
            ]
        ),
    )


GeodisMessagerieTotalCost = build_total_cost(
    messagerie_tp,
    cost_by_unit=MyCostByBottleCalculator(messagerie_tp),
    palet_cost=FixedCostByExpe(
        name=CostType.Palet, palet_cost=messagerie_tp.palet_movement_cost
    ),
)

GeodisPaletteTotalCost = build_total_cost(
    palette_tp,
    cost_by_unit=MyCostByPaletCalculator(palette_tp),
    palet_cost=CostByPaletCalculator(
        cost_by_palet=palette_tp.cost_by_palet,
        max_palet_weight=palette_tp.max_palet_weight,
        palet_weight=palette_tp.palet_weight,
    ),
)

if __name__ == "__main__":
    from src.constant import BOTTLE, Package

    expedition = MultiRefExpedition(
        [SingleRefExpedition(n_bottles=30, bottle_type=BOTTLE, package=Package())]
    )
    for total_cost in (GeodisMessagerieTotalCost, GeodisPaletteTotalCost):
        print(
            total_cost.compute_cost(
                gnr_factor=14.89,
                expedition=expedition,
                department="73",
                postal_code="73000",
                agg=False,
            )
        )
