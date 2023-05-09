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

BOTTLE_BY_PACKAGE = 6
PACKAGE_WEIGHT = 8

DATA_FOLDER = Path(r"../data")
