from abc import ABC, abstractmethod
from typing import Union

import pandas as pd

from src.constant import TarifType, UnitType
from src.cost_calculator import (
    BaseCostCalculator,
    MultiRefExpedition,
    SingleRefExpedition,
    round_cost,
)
from src.cost_calculator.constant import CostType
from src.file_structure import TarifDeptFile, TarifStructureFile
from src.transporter.transporter_params import AbstractTransporterParams


class CostByBottleCalculator(ABC, BaseCostCalculator):
    name: CostType = CostType.ByBottle

    def __init__(self, transporter_params: AbstractTransporterParams):
        self.tarif_structure = pd.read_csv(
            transporter_params.data_folder / TarifStructureFile.name,
            **TarifStructureFile.csv_format,
            index_col=[TarifStructureFile.Cols.unit],
        )
        self.tarif_by_dep = pd.read_csv(
            transporter_params.data_folder / TarifDeptFile.name,
            **TarifDeptFile.csv_format,
            index_col=[TarifDeptFile.Cols.dpt],
        )

    @staticmethod
    @abstractmethod
    def _get_dpt_code(series_of_dpt: pd.Series) -> pd.Series:
        pass

    @abstractmethod
    def _get_tarif_unit(
        self, expedition: Union[SingleRefExpedition, MultiRefExpedition]
    ) -> tuple[UnitType, int]:
        """
        Get the tarif unit type from the number of bottles in the expedition
        :param expedition: Single ref or Multi ref expedition
        :return: tarif unit and number of corresponding units (bottle or palet)
        """
        pass

    def _get_tarif_info(self, n_unit: int, tarif_unit: UnitType) -> pd.DataFrame:
        tarif_structure = self.tarif_structure.loc[tarif_unit]
        min_volume_condition = tarif_structure[TarifStructureFile.Cols.min_] <= n_unit
        max_volume_condition = tarif_structure[TarifStructureFile.Cols.max_] >= n_unit
        return tarif_structure[min_volume_condition & max_volume_condition]

    def get_tarif_conditions(
        self, expedition: Union[SingleRefExpedition, MultiRefExpedition]
    ) -> tuple[int, UnitType, TarifType, str]:
        tarif_unit, n_unit = self._get_tarif_unit(expedition)
        tarif_info = self._get_tarif_info(n_unit, tarif_unit)
        tarif_type, tarif_id = tarif_info.loc[
            tarif_unit,
            [TarifStructureFile.Cols.type_, TarifStructureFile.Cols.tarif_id],
        ]
        return n_unit, tarif_unit, tarif_type, tarif_id

    def _compute_cost_nationwide(
        self, expedition: Union[SingleRefExpedition, MultiRefExpedition]
    ) -> pd.DataFrame:
        n_unit, tarif_unit, tarif_type, tarif_id = self.get_tarif_conditions(expedition)
        cost = self.tarif_by_dep[tarif_id].to_frame(name=n_unit)
        if tarif_type == TarifType.VARIABLE:
            cost *= n_unit
        return cost

    @round_cost()
    def compute_cost(
        self, expedition: MultiRefExpedition, department: str, *args, **kwargs
    ) -> float:
        nation_wide_cost = self._compute_cost_nationwide(expedition)
        nation_wide_cost.index = self._get_dpt_code(nation_wide_cost.index)
        return nation_wide_cost.loc[department].item()
