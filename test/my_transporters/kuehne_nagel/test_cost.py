import pandas as pd
import pytest

from src.constant import TarifType, UnitType
from src.cost_calculator.expedition import SingleRefExpedition
from src.my_transporters.kuehne_nagel.cost import KNGCostByBottleCalculator


class TestCostByBottle:
    cost_calc = KNGCostByBottleCalculator()

    @pytest.mark.parametrize("n_col", [30, 150, 1000])
    def test_get_tarif_unit(self, n_col):
        assert self.cost_calc._get_tarif_unit(SingleRefExpedition(n_bottles=n_col)) == (
            UnitType.BOTTLE,
            n_col,
        )

    @pytest.mark.parametrize(
        ("n_col", "valid_unit", "valid_tarif", "valid_id"),
        [
            (6, UnitType.BOTTLE, TarifType.FORFAIT, "Tarif 1"),
            (15, UnitType.BOTTLE, TarifType.FORFAIT, "Tarif 2"),
            (21, UnitType.BOTTLE, TarifType.FORFAIT, "Tarif 3"),
            (450, UnitType.BOTTLE, TarifType.VARIABLE, "Tarif 12"),
        ],
    )
    def test_get_tarif_conditions(
        self, n_col: int, valid_unit: UnitType, valid_tarif: TarifType, valid_id: str
    ):
        n_unit, t_unit, t_type, t_id = self.cost_calc.get_tarif_conditions(
            SingleRefExpedition(n_bottles=n_col)
        )
        assert t_unit == valid_unit
        assert t_type == valid_tarif
        assert t_id == valid_id

    @pytest.mark.parametrize(("n_col", "total_cost"), [])
    def test_compute_cost_nationwide_forfait(self, n_col, total_cost):
        cost = self.cost_calc._compute_cost_nationwide(
            expedition=SingleRefExpedition(n_bottles=n_col)
        )
        assert isinstance(cost, pd.DataFrame)
        assert round(cost[n_col].sum(), 2) == total_cost

    @pytest.mark.parametrize(("n_col", "unit_cost"), [])
    def test_compute_cost_nationwide_variable(self, n_col, unit_cost):
        cost = self.cost_calc._compute_cost_nationwide(
            expedition=SingleRefExpedition(n_bottles=n_col)
        )
        assert isinstance(cost, pd.DataFrame)
        assert cost[n_col].sum() == unit_cost * n_col
