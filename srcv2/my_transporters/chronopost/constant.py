from typing import Final
from dataclasses import dataclass, field
from srcv2.transporter.transporter_params import AbstractTransporterParams
from srcv2.cost_calculator.cost_by_package import ExtraPackageCost


@dataclass(kw_only=True)
class TransporterParams(AbstractTransporterParams):
    name: Final[str] = "Chronopost"

    extra_kg_cost: float = 1.13  # Frais par kg supplémentaire au dela de 15 kg - Chronopost

    extra_package_cost: ExtraPackageCost = field(default_factory=lambda: ExtraPackageCost(
        extra_package_cost=0.89,  # Frais par colis (sureté + ecolo - Chronopost
        max_free_package=0,  # Nombre de colis max sans frais multi-colis - Chronopost
        multi_package_max_fee=9999,  # Coût max de la gestion multi-colis - Chronopost
    ))

    default_gas_factor: float = 17.55
    gas_modulation_link: str = "https://www.chronopost.fr/fr/surcharge-carburant"

    max_bottles: int = 100  # Quantité arbitraire
