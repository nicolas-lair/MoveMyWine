from enum import Enum
from pathlib import Path


class TarifType(str, Enum):
    FORFAIT = "Forfait"
    VARIABLE = "Variable"


class UnitType(str, Enum):
    BOTTLE = "Col"
    PALET = "Palette"
    KG = "Kg"


CSV_PARAMS = {
    "sep": ";",
    "decimal": ".",
    "encoding": "utf-8",
}


class Bottle:
    volume = 0.75  # L
    weight = 1.4  # Kg


class Package:
    box_weight = 0.6  # Kg
    bottle_by_package = 6
    package_weight = 8.5  # Kg

    def get_package_weight(self, bottle: Bottle):
        return self.bottle_by_package * bottle.weight + self.box_weight


N_EXPEDITION = 5

DATA_FOLDER = Path(r"../data")
