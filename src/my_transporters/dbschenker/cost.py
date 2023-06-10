from pathlib import Path
import pandas as pd

from src.cost_calculator import *
from src.file_structure import TarifStructureFile, TarifZoneFile, CorrespondanceZoneDpt

from .constant import TransporterParams

tp = TransporterParams()


class MyCostByBottleCalculator(CostByBottleCalculator):
    def __init__(self, data_folder: Path):
        self.tarif_structure = pd.read_csv(
            data_folder / TarifStructureFile.name,
            **TarifStructureFile.csv_format,
            index_col=[TarifStructureFile.Cols.unit]
        )
        self.tarif_by_zone = pd.read_csv(
            data_folder / TarifZoneFile.name,
            **TarifZoneFile.csv_format,
            index_col=[TarifZoneFile.Cols.zone]
        )
        self.correspondance_zone_dpt = pd.read_csv(
            data_folder / CorrespondanceZoneDpt.name,
            **CorrespondanceZoneDpt.csv_format,
            index_col=[CorrespondanceZoneDpt.Cols.zone]
        )

        self.tarif_by_dep = pd.merge(
            self.tarif_by_zone, self.correspondance_zone_dpt,
            right_index=True, left_index=True
        )
        self.tarif_by_dep = self.tarif_by_dep.set_index(CorrespondanceZoneDpt.Cols.dpt)
        self.cost_by_dest_and_volume = super().compute_cost_by_destination_and_volume()

    @staticmethod
    def _get_dpt_code(dpt_series: pd.Series) -> pd.Series:
        return dpt_series


class DBSchenkerTotalCost(TotalCostCalculator):
    costs = {
        CostType.ByBottle: GasModulatedCost(MyCostByBottleCalculator(data_folder=tp.data_folder), True),
        CostType.ByPackage: GasModulatedCost(CostByPackageCalculator(), True),
        CostType.Expedition: GasModulatedCost(FixedCostByExpeditionCalculator(**tp.expedition_cost), True),
        CostType.Monthly: GasModulatedCost(MonthlyCostCalculator(**tp.monthly_cost), False)
    }
