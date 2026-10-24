from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Final

from src.constant import EURO_PALET_WEIGHT
from src.cost_calculator.cost_by_package import ExtraPackageCost
from src.file_structure import MapZone2PostalCode
from src.transporter.transporter_params import (
    AbstractTransporterParams,
    ModulatorConfig,
)


@dataclass(kw_only=True)
class GeodisParams(AbstractTransporterParams):
    """Parameters shared by all Geodis offers (messagerie, palette)"""

    tarif_folder: ClassVar[str]  # Sub-folder of data/geodis holding the offer tarif

    extra_package_cost: ExtraPackageCost = field(
        default_factory=lambda: ExtraPackageCost(
            extra_package_cost=0.6,  # Frais par colis
            max_free_package=10,  # Nombre de colis max sans frais multi-colis - Geodis
            multi_package_max_fee=25,  # Coût max de la gestion multi-colis - Geodis
        )
    )

    extra_destination_cost: dict = field(
        default_factory=lambda: {
            "postalcode2zone": MapZone2PostalCode(
                name="livraison_zones_urbaines_contraintes_detail.csv"
            ),
            "weight_limit": [30, 100],
            "cost": {
                "Zone A": [2, 2, 2],
                "Zone B": [3.3, 6.6, 10.15],
            },
        }
    )

    surete_cost = 2.15

    modulators: ClassVar[dict[str, ModulatorConfig]] = {
        "GNR": ModulatorConfig(
            modulation_link="https://geodis.com/fr/transport-de-marchandises/transport-de-colis-et-de-palettes/taux-de-surcharge-energie",
            arg_name="gnr_factor",
            min_value=0.0,
            default=0.0,
            max_value=100.0,
            input_format="%2.f",
        )
    }

    @property
    def modulator_prefix(self) -> str:
        return "geodis"  # Same surcharge for all Geodis offers

    @property
    def common_data_folder(self) -> Path:
        return Path(__file__).parents[3] / "data" / "geodis"

    @property
    def data_folder(self) -> Path:
        return self.common_data_folder / self.tarif_folder


@dataclass(kw_only=True)
class MessagerieParams(GeodisParams):
    name: Final[str] = "Geodis Messagerie"
    tarif_folder: ClassVar[str] = "messagerie"

    palet_movement_cost: float = 5.0  # Gestion des palettes Europe, par expédition


@dataclass(kw_only=True)
class PaletteParams(GeodisParams):
    name: Final[str] = "Geodis Palette"
    tarif_folder: ClassVar[str] = "palette"

    max_palet_weight: int = 700  # kg, poids brut palette incluse
    palet_weight: float = EURO_PALET_WEIGHT  # kg
    cost_by_palet: float = 10.0  # Frais par palette, à confirmer avec Geodis
