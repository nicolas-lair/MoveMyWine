from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass
class ModulatorConfig:
    modulation_link: str
    arg_name: str
    min_value: float
    default: float
    max_value: float
    input_format: str
    modulation_file: str | None = None


@runtime_checkable
class TransporterParamsProtocol(Protocol):
    name: str
    modulators: dict[str, ModulatorConfig]
    data_folder: Path | Callable[[], Path]


class AbstractTransporterParams(TransporterParamsProtocol):
    @property
    def data_folder(self) -> Path:
        return Path(__file__).parents[2] / "data" / self.name.lower()

    @property
    def modulator_prefix(self) -> str:
        """Transporters with the same prefix share their modulator values"""
        return self.name.lower()

    def modulator_key(self, mod_name: str) -> str:
        """Session state key holding the modulator value"""
        return f"{self.modulator_prefix}_{mod_name.lower()}_modulator"
