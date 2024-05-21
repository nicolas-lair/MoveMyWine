from typing import Final
from dataclasses import dataclass, field
from src.transporter.transporter_params import (
    AbstractTransporterParams,
    ModulatorConfig,
)
from src.cost_calculator.cost_by_package import ExtraPackageCost


@dataclass(kw_only=True)
class TransporterParams(AbstractTransporterParams):
    name: Final[str] = "Chronopost"

    extra_kg_cost: float = (
        1.13  # Frais par kg supplémentaire au dela de 15 kg - Chronopost
    )

    extra_package_cost: ExtraPackageCost = field(
        default_factory=lambda: ExtraPackageCost(
            extra_package_cost=0.89,  # Frais par colis (sureté + ecolo - Chronopost
            max_free_package=0,  # Nombre de colis max sans frais multi-colis - Chronopost
            multi_package_max_fee=9999,  # Coût max de la gestion multi-colis - Chronopost
        )
    )

    fixed_cost: dict = field(
        default_factory=lambda: {
            "surete": 0.8,
            "eco": 0.09,
        }
    )

    modulators = {
        "GNR": ModulatorConfig(
            modulation_link="https://www.chronopost.fr/fr/surcharge-carburant",
            arg_name="gnr_factor",
            min_value=0.0,
            max_value=100.0,
            input_format="%2.f",
        )
    }
