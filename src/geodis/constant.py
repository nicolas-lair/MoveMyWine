from typing import Final
from src.app_generics.transporter_params import AbstractTransporterParams, ExtraPackageCost


class TransporterParams(AbstractTransporterParams):
    name: Final[str] = "Geodis"

    extra_package_cost = ExtraPackageCost(
        extra_package_cost=0.55,  # Frais multi-colis (par colis) - GEODS
        max_free_package=10,  # Nombre de colis max sans frais multi-colis - GEODIS
        multi_package_max_fee=25  # Coût max de la gestion multi-colis - GEODIS
    )

    expedition_cost = {
        "securite": 2.15

    }

    monthly_cost = {
        "facturation": 13,
    }

    default_gas_factor = 15.57
    gas_modulation_link = "https://geodis.com/fr/gestion-du-fret/transport-terrestre/transport-de-palettes-et-de-colis/taux-de-surcharge-carburant"
