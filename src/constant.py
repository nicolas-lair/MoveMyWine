from enum import Enum


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
