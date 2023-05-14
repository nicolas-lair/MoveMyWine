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

    def _get_dpt_code(self, dpt_series: pd.Series) -> pd.Series:
        return dpt_series


class MyTransporter(AbstractTransporter):
    def __init__(self):
        self.costByBottle = MyCostByBottleCalculator(data_folder=tp.data_folder)
        self.costByExpeditionObject = FixedCostByExpeditionCalculator(**tp.expedition_cost)
        self.monthlyCost = MonthlyCostCalculator(**tp.monthly_cost)

    def get_total_cost(self, department: str, gas_factor: float, n_client: int = None, **kwargs) -> pd.DataFrame:
        return super().get_total_cost(department=department, gas_factor=1, n_client=n_client, **kwargs)
