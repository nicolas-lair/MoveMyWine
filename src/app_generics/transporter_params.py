from pathlib import Path
from dataclasses import dataclass
from src.constant import DATA_FOLDER


@dataclass
class ExtraPackageCost:
    extra_package_cost: float = 0  # No cost by default
    max_free_package: int = 0  # No cost by default
    multi_package_max_fee: float = 0  # No cost by default


class AbstractTransporterParams:
    name: str

    expedition_cost = dict()
    monthly_cost = dict()

    extra_kg_cost: float

    extra_package_cost: ExtraPackageCost

    default_gas_factor: float
    gas_modulation_link: str

    @property
    def data_folder(self) -> Path:
        return DATA_FOLDER / self.name.lower()

    def __init__(self, *args, **kwargs):
        """ For cooperative multiple inheritance """
        super().__init__(*args, **kwargs)
