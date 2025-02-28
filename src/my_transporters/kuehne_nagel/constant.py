from typing import Final
from dataclasses import dataclass

from src.transporter.transporter_params import (
    AbstractTransporterParams,
    ModulatorConfig,
)


@dataclass(kw_only=True)
class TransporterParams(AbstractTransporterParams):
    name: Final[str] = "Kuehne-Nagel"
    # TODO check that
    max_palet_weight: int = 600

    position_cost: float = 0.0
    security_cost: float = 1.9

    modulators = {
        "GNR": ModulatorConfig(
            modulation_link="https://www.cnr.fr/espaces/13/indicateurs/43",
            modulation_file="gnr_modulation.csv",
            arg_name="gnr_factor",
            min_value=0.7,
            default=1.0,
            max_value=2.6,
            input_format="%4.f",
        ),
    }
