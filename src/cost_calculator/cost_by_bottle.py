from abc import abstractmethod, ABC

from pathlib import Path

import pandas as pd

from src.constant import UnitType, TarifType
from src.file_structure import TarifStructureFile, TarifDeptFile


class CostByBottleCalculator(ABC):
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

    def _get_tarif_id(self, bottles: int) -> (pd.Series, int):
        min_volume_condition = (self.tarif_structure[TarifStructureFile.Cols.min_] <= bottles)
        max_volume_condition = (self.tarif_structure[TarifStructureFile.Cols.max_] >= bottles)
        return self.tarif_structure[min_volume_condition & max_volume_condition], bottles

    @property
    def max_bottles(self) -> int:
        max_bottles = self.tarif_structure.loc[UnitType.BOTTLE, TarifStructureFile.Cols.max_].max()
        return max_bottles

    def compute_cost_nationwide(self, n_bottles: int) -> pd.Series:
        tarif_id, volume_in_tarif_unit = self._get_tarif_id(bottles=n_bottles)
        cost = self.tarif_by_dep[tarif_id[TarifStructureFile.Cols.tarif_id].item()].to_frame(n_bottles)
        if tarif_id.Type.item() == TarifType.VARIABLE:
            cost *= volume_in_tarif_unit
        return cost

    def compute_cost_by_destination_and_volume(self) -> pd.DataFrame:
        cost = pd.concat(
            [self.compute_cost_nationwide(n_bottles=i) for i in range(1, self.max_bottles + 1)],
            axis=1
        )
        cost = cost.set_index(self._get_dpt_code(cost.index))
        return cost

    def compute_cost(self, *args, **kwargs):
        return self.cost_by_dest_and_volume
