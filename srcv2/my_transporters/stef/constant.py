from typing import Final
from dataclasses import dataclass

from srcv2.transporter.transporter_params import AbstractTransporterParams


@dataclass(kw_only=True)
class TransporterParams(AbstractTransporterParams):
    name: Final[str] = "Stef"
    max_palet_weight: int = 600

    position_cost: float = 5.2
    security_cost: float = 0.7

    gas_modulation_link: str = "https://www.cnr.fr/espaces/13/indicateurs/41"
