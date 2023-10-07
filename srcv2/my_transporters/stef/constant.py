import dataclasses
from typing import Final
from src.transporter.transporter_params import AbstractTransporterParams


class TransporterParams(AbstractTransporterParams):
    name: Final[str] = "Stef"
    max_palet_weight = 600

    position_cost=5.2
    security_cost=0.7


    gas_modulation_link = "https://www.cnr.fr/espaces/13/indicateurs/41"
