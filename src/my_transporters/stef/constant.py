from typing import Final
from dataclasses import dataclass

from src.transporter.transporter_params import AbstractTransporterParams


@dataclass(kw_only=True)
class TransporterParams(AbstractTransporterParams):
    name: Final[str] = "Stef"
    max_palet_weight: int = 600

    position_cost: float = 5.2
    security_cost: float = 0.7

    gnr_modulation_link: str = "https://www.cnr.fr/espaces/13/indicateurs/41"
    _gnr_modulation_file: str = "gnr_modulation.csv"
    gnr_arg_name = "gnr_factor"

    cold_modulation_link: str = "https://www.cnr.fr/espaces/13/indicateurs/36"
    _cold_modulation_file: str = "modulation_froid.csv"
    cold_arg_name = "cold_factor"

    def __post_init__(self):
        self.gnr_modulation_file = self.data_folder / self._gnr_modulation_file
        self.cold_modulation_file = self.data_folder / self._cold_modulation_file
