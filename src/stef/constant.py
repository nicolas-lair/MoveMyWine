from typing import Final
from src.app_generics.transporter_params import AbstractTransporterParams


class TransporterParams(AbstractTransporterParams):
    name: Final[str] = "Stef"
    max_palet_weight = 600

    expedition_cost = dict(
        position=5.2,
        security=0.7
    )

    gas_modulation_link = "https://www.cnr.fr/espaces/13/indicateurs/41"
