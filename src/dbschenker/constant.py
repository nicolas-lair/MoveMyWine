from typing import Final
from src.app_generics.transporter_params import AbstractTransporterParams


class TransporterParams(AbstractTransporterParams):
    name: Final[str] = "DBSchenker"

    expedition_cost = {
        "securite": 2.21

    }

    monthly_cost = {
        "facturation": 24.56,
    }

    gas_modulation_link = "https://geodis.com/fr/gestion-du-fret/transport-terrestre/transport-de-palettes-et-de-colis/taux-de-surcharge-carburant"
