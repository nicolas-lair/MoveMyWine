import pandas as pd
import pytest

from src.cost_calculator.expedition import SingleRefExpedition
from src.my_transporters.stef.cost import StefCostByBottleCalculator
from src.constant import UnitType, TarifType


class TestCostByBottle:
    cost_calc = StefCostByBottleCalculator()

    @pytest.mark.parametrize("n_col", [30, 198])
    def test_get_tarif_unit(self, n_col):
        assert self.cost_calc._get_tarif_unit(n_col) == UnitType.BOTTLE

    def test_max_unit_tarif(self):
        with pytest.raises(NotImplementedError):
            _ = self.cost_calc._get_tarif_unit(199)

    @pytest.mark.parametrize(
        ("n_col", "valid_unit", "valid_tarif", "valid_id"),
        [
            (30, UnitType.BOTTLE, TarifType.FORFAIT, "Tarif 1"),
            (78, UnitType.BOTTLE, TarifType.FORFAIT, "Tarif 2"),
            (79, UnitType.BOTTLE, TarifType.VARIABLE, "Tarif 3"),
        ],
    )
    def test_get_tarif_conditions(
        self, n_col: int, valid_unit: UnitType, valid_tarif: TarifType, valid_id: str
    ):
        t_unit, t_type, t_id = self.cost_calc.get_tarif_conditions(n_col)
        assert t_unit == valid_unit
        assert t_type == valid_tarif
        assert t_id == valid_id

    @pytest.mark.parametrize(("n_col", "total_cost"), [(30, 3070.97)])
    def test_compute_cost_nationwide_forfait(self, n_col, total_cost):
        cost = self.cost_calc._compute_cost_nationwide(
            expedition=SingleRefExpedition(n_bottles=n_col)
        )
        assert isinstance(cost, pd.DataFrame)
        assert round(cost[n_col].sum(), 2) == total_cost

    @pytest.mark.parametrize(("n_col", "unit_cost"), [(79, 63.92)])
    def test_compute_cost_nationwide_variable(self, n_col, unit_cost):
        cost = self.cost_calc._compute_cost_nationwide(
            expedition=SingleRefExpedition(n_bottles=n_col)
        )
        assert isinstance(cost, pd.DataFrame)
        assert cost[n_col].sum() == unit_cost * n_col
