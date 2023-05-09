from pathlib import Path

import pandas as pd

from src.constant import UnitType, TarifType
from src.file_structure import TarifStructureFile, TarifDeptFile


class CostByBottleCalculator:
    def __init__(self, data_folder: Path):
        self.tarif_structure = pd.read_csv(
            data_folder / TarifStructureFile.name,
            **TarifStructureFile.csv_format,
            index_col=[TarifStructureFile.Cols.unit]
        )
        self.tarif_dep = pd.read_csv(
            data_folder / TarifDeptFile.name,
            **TarifDeptFile.csv_format,
            index_col=[TarifDeptFile.Cols.dpt]
        )

    def _get_tarif_id(self, unit: UnitType, volume: int) -> pd.Series:
        tarif_type = self.tarif_structure.loc[unit]
        return tarif_type[
            (tarif_type[TarifStructureFile.Cols.min_] <= volume)
            & (tarif_type[TarifStructureFile.Cols.max_] >= volume)
            ]

    def _batch_compute(self, unit: UnitType, volume: int) -> pd.Series:
        tarif = self._get_tarif_id(unit=unit, volume=volume)
        cost = self.tarif_dep[tarif[TarifStructureFile.Cols.tarif].item()].to_frame(volume)
        if tarif.Type.item() == TarifType.VARIABLE:
            cost *= volume
        return cost

    def compute_bottle_cost_nationwide(self, n_bottles: int):
        return self._batch_compute(unit=UnitType.BOTTLE, volume=n_bottles)

    def compute_palet_cost_nationwide(self, n_palets: int):
        return self._batch_compute(unit=UnitType.PALET, volume=n_palets)
