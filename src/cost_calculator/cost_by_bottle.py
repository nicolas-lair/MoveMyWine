from abc import abstractmethod

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
        self.tarif_by_dep = pd.read_csv(
            data_folder / TarifDeptFile.name,
            **TarifDeptFile.csv_format,
            index_col=[TarifDeptFile.Cols.dpt]
        )
        self.cost_by_dest_and_volume = self.compute_cost_by_destination_and_volume()

    @abstractmethod
    def _get_dpt_code(self, series_of_dpt: pd.Series) -> pd.Series:
        pass

    def _get_tarif_id(self, volume: int) -> pd.Series:
        min_volume_condition = (self.tarif_structure[TarifStructureFile.Cols.min_] <= volume)
        max_volume_condition = (self.tarif_structure[TarifStructureFile.Cols.max_] >= volume)
        return self.tarif_structure[min_volume_condition & max_volume_condition]

    @property
    def max_bottles(self) -> int:
        max_bottles = self.tarif_structure.loc[UnitType.BOTTLE, TarifStructureFile.Cols.max_].max()
        return max_bottles

    def _compute_cost(self, volume: int) -> pd.Series:
        tarif_id = self._get_tarif_id(volume=volume)
        cost = self.tarif_by_dep[tarif_id[TarifStructureFile.Cols.tarif].item()].to_frame(volume)
        if tarif_id.Type.item() == TarifType.VARIABLE:
            cost *= volume
        return cost

    def compute_bottle_cost_nationwide(self, n_bottles: int):
        return self._compute_cost(volume=n_bottles)

    def compute_cost_by_destination_and_volume(self) -> pd.DataFrame:
        cost = pd.concat(
            [self.compute_bottle_cost_nationwide(n_bottles=i) for i in range(self.max_bottles + 1)],
            axis=1
        )
        cost["dpt_code"] = self._get_dpt_code(cost.index)
        return cost
