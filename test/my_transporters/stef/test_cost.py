import pandas as pd
import pytest

from src.constant import TarifType, UnitType
from src.cost_calculator.expedition import SingleRefExpedition
from src.my_transporters.stef.cost import StefCostByBottleCalculator


class TestCostByBottle:
    cost_calc = StefCostByBottleCalculator()

    @pytest.mark.parametrize(
        ("n_col", "unit_type", "n_unit"),
        [
            (30, UnitType.BOTTLE, 30),
            (198, UnitType.BOTTLE, 198),
            (199, UnitType.PALET, 1),
            (300, UnitType.PALET, 1),
            (600, UnitType.PALET, 2),
        ],
    )
    def test_get_tarif_unit(self, n_col, unit_type, n_unit):
        assert self.cost_calc._get_tarif_unit(SingleRefExpedition(n_bottles=n_col)) == (
            unit_type,
            n_unit,
        )

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
        n_unit, t_unit, t_type, t_id = self.cost_calc.get_tarif_conditions(
            SingleRefExpedition(n_bottles=n_col)
        )
        assert t_unit == valid_unit
        assert t_type == valid_tarif
        assert t_id == valid_id

    @pytest.mark.parametrize(("n_col", "total_cost"), [(30, 3243.55)])
    def test_compute_cost_nationwide_forfait(self, n_col, total_cost):
        cost = self.cost_calc._compute_cost_nationwide(
            expedition=SingleRefExpedition(n_bottles=n_col)
        )
        assert isinstance(cost, pd.DataFrame)
        assert round(cost[n_col].sum(), 2) == total_cost

    # unit_cost is the sum of the prices for all departments (and relivraison) for given number of bottles
    @pytest.mark.parametrize(("n_col", "unit_cost"), [(79, 67.49)])
    def test_compute_cost_nationwide_variable(self, n_col, unit_cost):
        cost = self.cost_calc._compute_cost_nationwide(
            expedition=SingleRefExpedition(n_bottles=n_col)
        )
        assert isinstance(cost, pd.DataFrame)
        assert cost[n_col].sum() == unit_cost * n_col
