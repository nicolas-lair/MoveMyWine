from enum import Enum


class CostType(str, Enum):
    Expedition = "Frais Expédition"
    Security = "Frais Sécurité"
    Palet = "Frais Palette"
    ByBottle = "Coût Bouteilles"
    ByPackage = "Coût Colis"
    Monthly = "Coût Mensuel"
    Total = "Coût Total"

    GNRMod = "Surcoût GNR"
    ColdMod = "Surcoût Groupe Froid"
