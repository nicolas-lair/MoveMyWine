from pathlib import Path
import functools
import pandas as pd

from src.file_structure import GasModulationFile


class GasModulatorFromPrice:
    def __init__(self, data_folder: Path):
        self.gas_modulation = pd.read_csv(
            data_folder / GasModulationFile.name,
            **GasModulationFile.csv_format
        )
        self.gas_modulation[GasModulationFile.Cols.modulation] = (
            self.gas_modulation[GasModulationFile.Cols.modulation]
            .str.replace("%", "")
            .astype(int)
            .div(100)
            .add(1)
        )

    def get_modulation_factor(self, gas_price: float):
        min_condition = self.gas_modulation[GasModulationFile.Cols.min_price] <= gas_price
        max_condition = self.gas_modulation[GasModulationFile.Cols.max_price] >= gas_price
        factor = (
            self.gas_modulation
            .loc[min_condition & max_condition, GasModulationFile.Cols.modulation]
            .item()
        )
        return factor
