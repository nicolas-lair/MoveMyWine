from collections import UserDict
from typing import Union

from .constant import CostType
from .base_cost import BaseCost
from .expedition import MultiRefExpedition, SingleRefExpedition


class CostCollectionCalculator(UserDict[CostType, BaseCost]):
    def compute_cost(
        self,
        expedition: Union[SingleRefExpedition, MultiRefExpedition],
        **kwargs,
    ) -> dict[CostType, float]:
        if expedition.n_bottles == 0:
            detailed_cost = {k: 0 for k in self.keys()}
        else:
            detailed_cost = {
                k: cc.compute_cost(expedition=expedition, **kwargs)
                for k, cc in self.items()
            }
        return detailed_cost
