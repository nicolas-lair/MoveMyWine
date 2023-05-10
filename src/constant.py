from enum import Enum
from pathlib import Path


class TarifType(str, Enum):
    FORFAIT = "Forfait"
    VARIABLE = "Variable"


class UnitType(str, Enum):
    BOTTLE = "Col"
    PALET = "Palette"


CSV_PARAMS = {
    "sep": ";",
    "decimal": ".",
    "encoding": "utf-8",
}


class Package:
    bottle_by_package = 6
    package_weight = 8
    max_package_without_palet = 15


N_EXPEDITION = 5

DATA_FOLDER = Path(r"../data")
