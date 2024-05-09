import dataclasses
from pathlib import Path


@dataclasses.dataclass(kw_only=True)
class AbstractTransporterParams:
    name: str = ""

    default_gas_factor: float = None
    gnr_modulation_link: str = ""

    @property
    def data_folder(self) -> Path:
        return Path(__file__).parents[2] / "data" / self.name.lower()
