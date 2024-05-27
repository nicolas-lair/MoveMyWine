from dataclasses import dataclass
from enum import Enum
from typing import Optional
from math import ceil


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


class BaseBottle:
    def __init__(self, empty_weight, volume, bottle_eq: Optional[int] = None):
        self.empty_weight = empty_weight  # Kg
        self.volume = volume  # L
        self.bottle_eq = ceil(self.volume // 0.75) if bottle_eq is None else bottle_eq

    @property
    def weight(self):
        return self.empty_weight + self.volume


BOTTLE = BaseBottle(empty_weight=0.380, volume=0.75, bottle_eq=1)
MAGNUM = BaseBottle(empty_weight=1.0, volume=1.5, bottle_eq=2)


@dataclass(kw_only=True)
class Package:
    box_weight: float = 0.6
    bottle_by_package: int = 6
    # def __init__(self, box_weight=0.6, bottle_by_package=6):
    #     self.box_weight = box_weight  # Kg
    #     self.bottle_by_package = bottle_by_package #


N_EXPEDITION = 5
