from typing import Protocol, runtime_checkable, Optional, Callable

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ModulatorConfig:
    modulation_link: str
    arg_name: str
    min_value: float
    max_value: float
    input_format: str
    modulation_file: Optional[str] = None


@runtime_checkable
class TransporterParamsProtocol(Protocol):
    name: str
    modulators: dict[str, ModulatorConfig]
    data_folder: Path | Callable[[], Path]


class AbstractTransporterParams(TransporterParamsProtocol):
    @property
    def data_folder(self) -> Path:
        return Path(__file__).parents[2] / "data" / self.name.lower()
