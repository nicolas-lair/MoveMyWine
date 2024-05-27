from typing import Final
from dataclasses import dataclass

from src.transporter.transporter_params import (
    AbstractTransporterParams,
    ModulatorConfig,
)


@dataclass(kw_only=True)
class TransporterParams(AbstractTransporterParams):
    name: Final[str] = "Stef"
    max_palet_weight: int = 600

    position_cost: float = 5.2
    security_cost: float = 0.7

    modulators = {
        "GNR": ModulatorConfig(
            modulation_link="https://www.cnr.fr/espaces/13/indicateurs/41",
            modulation_file="gnr_modulation.csv",
            arg_name="gnr_factor",
            min_value=0.0,
            default=1.0,
            max_value=2.0,
            input_format="%4.f",
        ),
        "Froid": ModulatorConfig(
            modulation_link="https://www.cnr.fr/espaces/13/indicateurs/36",
            modulation_file="modulation_froid.csv",
            arg_name="cold_factor",
            min_value=0.0,
            default=300.0,
            max_value=750.0,
            input_format="%.2f",
        ),
    }
