from typing import Protocol, runtime_checkable

from src.transporter import AbstractTransporterParams, ModulatorConfig
from src.cost_calculator import TotalCostCalculator
from .fetched_indicator import FetchedIndicator


def validate_transporter(func):
    def wrapper(*args, **kwargs):
        # Check that the right class is used
        # assert isinstance(st.session_state.cost_calculator, func.__self__.__class__)
        return func(*args, **kwargs)

    return wrapper


@runtime_checkable
class TransporterApp(Protocol):
    cost_calculator: TotalCostCalculator
    params: AbstractTransporterParams

    @staticmethod
    def scrap_indicator(modconfig: ModulatorConfig) -> FetchedIndicator:
        ...

    def compute_cost(self) -> float:
        ...
