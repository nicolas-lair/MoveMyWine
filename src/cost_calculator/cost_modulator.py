from typing import Optional
from pathlib import Path
from dataclasses import dataclass

import pandas as pd

from .constant import CostType
from .base_cost import BaseCostCalculator, round_cost
from src.file_structure import ModulationFileConfig as ModFileConf


class ModulatorFromIndicator:
    def __init__(self, file_path: Path):
        modulation_config = ModFileConf(path=file_path)
        self.modulation = pd.read_csv(modulation_config.path, **ModFileConf.csv_format)
        self.modulation[ModFileConf.Cols.modulation] = (
            self.modulation[ModFileConf.Cols.modulation]
            .str.replace("%", "")
            .astype(float)
        )

    def get_mod_factor(self, indicator: float):
        min_condition = self.modulation[ModFileConf.Cols.lower_bound] <= indicator
        max_condition = self.modulation[ModFileConf.Cols.upper_bound] >= indicator
        factor = self.modulation.loc[
            min_condition & max_condition, ModFileConf.Cols.modulation
        ].item()
        return factor


@dataclass
class ModulatedCostCalculator(BaseCostCalculator):
    name: str
    modulated_cost: list[CostType]
    modulator_arg_name: str
    modulator_retriever: Optional[ModulatorFromIndicator] = None

    @round_cost()
    def compute_cost(self, cost_by_type: dict[CostType, float], **kwargs) -> float:
        modulator = kwargs[self.modulator_arg_name]
        cost_to_modulate = sum([cost_by_type[c] for c in self.modulated_cost], 0)
        if self.modulator_retriever is not None:
            modulator = self.modulator_retriever.get_mod_factor(indicator=modulator)
        modulated_cost = cost_to_modulate * (modulator / 100.0)
        return round(modulated_cost, 2)
