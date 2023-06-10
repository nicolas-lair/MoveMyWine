from typing import Final
from src.transporter.transporter_params import AbstractTransporterParams, ExtraPackageCost


class TransporterParams(AbstractTransporterParams):
    name: Final[str] = "Chronopost"

    extra_kg_cost = 1.13  # Frais par kg supplémentaire au dela de 15 kg - Chronopost

    extra_package_cost = ExtraPackageCost(
        extra_package_cost=0.89,  # Frais par colis (sureté + ecolo - Chronopost
        max_free_package=0,  # Nombre de colis max sans frais multi-colis - Chronopost
        multi_package_max_fee=9999,  # Coût max de la gestion multi-colis - Chronopost
    )

    expedition_cost = {
    }

    monthly_cost = {
        #     "facturation": 20,
    }

    default_gas_factor = 17.55
    gas_modulation_link = "https://www.chronopost.fr/fr/surcharge-carburant"

    max_bottles = 100  # Quantité arbitraire
