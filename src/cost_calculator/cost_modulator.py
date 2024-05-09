from typing import Optional
from pathlib import Path
from dataclasses import dataclass
from .constant import CostType

import pandas as pd

from src.file_structure import ModulationFileConfig as ModFileConf


class ModulatorFromIndicator:
    def __init__(self, file_path: Path):
        modulation_config = ModFileConf(path=file_path)
        self.modulation = pd.read_csv(modulation_config.path, **ModFileConf.csv_format)
        self.modulation[ModFileConf.Cols.modulation] = (
            self.modulation[ModFileConf.Cols.modulation]
            .str.replace("%", "")
            .astype(float)
            .div(100)
            .add(1)
        )

    def get_mod_factor(self, indicator: float):
        min_condition = self.modulation[ModFileConf.Cols.lower_bound] <= indicator
        max_condition = self.modulation[ModFileConf.Cols.upper_bound] >= indicator
        factor = self.modulation.loc[
            min_condition & max_condition, ModFileConf.Cols.modulation
        ].item()
        return factor


@dataclass
class ModulatedCostCollection:
    modulated_cost: list[CostType]
    modulator_arg_name: str
    modulator_retriever: Optional[ModulatorFromIndicator] = None

    def compute_cost(self, cost_by_type: dict[CostType, float], **kwargs) -> float:
        modulator = kwargs[self.modulator_arg_name]
        modulated_cost = sum([cost_by_type[c] for c in self.modulated_cost], 0)
        if self.modulator_retriever is not None:
            modulator = self.modulator_retriever.get_mod_factor(indicator=modulator)
        return modulated_cost * (modulator - 1)
