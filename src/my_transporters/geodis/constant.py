from dataclasses import dataclass, field
from typing import Final

from src.cost_calculator.cost_by_package import ExtraPackageCost
from src.transporter.transporter_params import (
    AbstractTransporterParams,
    ModulatorConfig,
)


@dataclass(kw_only=True)
class TransporterParams(AbstractTransporterParams):
    name: Final[str] = "Geodis"

    extra_package_cost: ExtraPackageCost = field(
        default_factory=lambda: ExtraPackageCost(
            extra_package_cost=0.6,  # Frais par colis
            max_free_package=10,  # Nombre de colis max sans frais multi-colis - Geodis
            multi_package_max_fee=25,  # Coût max de la gestion multi-colis - Geodis
        )
    )

    # extra_destination_cost: dict = field(default_factory=lambda : {
    #     "cost_by_": []
    #     "cost_by_zone": {
    #     "ZoneA": [1.9, 4.1, 6.2],
    #     "ZoneB": [3.4, 6.8, 10.4],}
    # })

    fixed_cost: dict = field(
        default_factory=lambda: {
            "surete": 2.2,
        }
    )

    modulators = {
        "GNR": ModulatorConfig(
            modulation_link="https://geodis.com/fr/transport-de-marchandises/transport-de-colis-et-de-palettes/taux-de-surcharge-energie",
            arg_name="gnr_factor",
            min_value=0.0,
            default=0.0,
            max_value=100.0,
            input_format="%2.f",
        )
    }
