from dataclasses import dataclass

from src.constant import EURO_PALET_WEIGHT

from .base_cost import BaseCostCalculator, round_cost
from .constant import CostType
from .expedition import MultiRefExpedition, SingleRefExpedition


@dataclass
class CostByPaletCalculator(BaseCostCalculator):
    cost_by_palet: float
    max_palet_weight: float
    palet_weight: float = EURO_PALET_WEIGHT
    name: CostType = CostType.Palet

    @round_cost()
    def compute_cost(
        self, expedition: SingleRefExpedition | MultiRefExpedition, **kwargs
    ) -> float:
        n_palets = expedition.n_palets(self.max_palet_weight, self.palet_weight)
        return n_palets * self.cost_by_palet
