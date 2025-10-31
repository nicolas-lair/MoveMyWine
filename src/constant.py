from dataclasses import dataclass
from enum import Enum
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


@dataclass(kw_only=True, frozen=True)
class BaseBottle:
    empty_weight: float  # kg
    volume: float = 0.75  # L

    @property
    def bottle_eq(self) -> int:
        return ceil(self.volume // 0.75)

    @property
    def weight(self):
        return self.empty_weight + self.volume


BOTTLE = BaseBottle(empty_weight=0.380, volume=0.75)
MAGNUM = BaseBottle(empty_weight=1.0, volume=1.5)


@dataclass(kw_only=True, frozen=True)
class Package:
    box_weight: float = 0.6
    bottle_by_package: int = 6
    bottle_type: BaseBottle = BOTTLE

    @property
    def weight(self) -> float:
        return self.box_weight + self.bottle_by_package * self.bottle_type.weight

    def compute_total_weight(self, n_bottles: int) -> float:
        n_package = ceil(n_bottles / self.bottle_by_package)
        return n_package * self.weight


MagnumPackage = Package(bottle_by_package=3, bottle_type=MAGNUM)
Bottle6Pack = Package()

N_EXPEDITION = 5
