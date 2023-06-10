from enum import Enum


class CostType(str, Enum):
    Expedition = "ExpeditionCost"
    ByBottle = "ByBottleCost"
    ByPackage = "ByPackageCost"
    Monthly = "MonthlyCost"
    Total = "TotalCost"
