import dataclasses
from typing import Dict
from pathlib import Path
from src.cost_calculator import ExtraPackageCost


class AbstractTransporterParams:
    name: str

    default_gas_factor: float = None

    expedition_cost: Dict[str, float] = dataclasses.field(default_factory=dict)
    monthly_cost: Dict[str, float] = dataclasses.field(default_factory=dict)

    extra_package_cost: ExtraPackageCost = ExtraPackageCost()
    gas_modulation_link: str = ""

    extra_kg_cost: float = 0

    @property
    def data_folder(self) -> Path:
        return Path(r"../data") / self.name.lower()
