import dataclasses

from src.cost_calculator import CostCollectionCalculator
from .transporter_params import AbstractTransporterParams


@dataclasses.dataclass
class Transporter:
    cost_calculator: CostCollectionCalculator
    transporter_config: AbstractTransporterParams
