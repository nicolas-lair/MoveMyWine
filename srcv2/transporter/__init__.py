import dataclasses

from srcv2.cost_calculator import TotalCostCalculator
from .transporter_params import AbstractTransporterParams
from srcv2.app_generics.dash_custom_component import DashCustomComponents


@dataclasses.dataclass
class Transporter:
    cost_calculator: TotalCostCalculator
    transporter_config: AbstractTransporterParams
    app_custom_component: DashCustomComponents
