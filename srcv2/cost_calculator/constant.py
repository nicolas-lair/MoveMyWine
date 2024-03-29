from enum import Enum


class CostType(str, Enum):
    Expedition = "ExpeditionCost"
    Security = "SecurityCost"
    ByBottle = "ByBottleCost"
    ByPackage = "ByPackageCost"
    Monthly = "MonthlyCost"
    Total = "TotalCost"
