from abc import ABC, abstractmethod

import pandas as pd


class AbstractCost(ABC):

    @abstractmethod
    def compute_cost_by_bottle(self, *args, **kwargs) -> pd.DataFrame:
        """ Compute cost for a range of number of bottles """
        ...

    @abstractmethod
    def compute_cost(self, n_bottles, *args, **kwargs) -> float:
        """ Compute cost for a given number of bottles"""
        ...
