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

    def test_compute_cost_nationwide_forfait(self):
        n_bottles = 30
        cost = self.cost_calc._compute_cost_nationwide(
            expedition=SingleRefExpedition(n_bottles=n_bottles)
        )
        assert isinstance(cost, pd.DataFrame)
        sum_tarif1 = 3070.97
        assert round(cost[n_bottles].sum(), 2) == sum_tarif1

    def test_compute_cost_nationwide_variable(self):
        n_bottles = 79
        cost = self.cost_calc._compute_cost_nationwide(
            expedition=SingleRefExpedition(n_bottles=n_bottles)
        )
        assert isinstance(cost, pd.DataFrame)
        sum_tarif3 = 63.92
        assert cost[n_bottles].sum() == sum_tarif3 * n_bottles
