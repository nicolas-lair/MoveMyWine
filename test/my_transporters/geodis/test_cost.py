import pytest

from src.constant import TarifType, UnitType
from src.cost_calculator.expedition import SingleRefExpedition
from src.my_transporters.geodis.cost import MyCostByBottleCalculator


class TestCostByBottle:
    cost_calc = MyCostByBottleCalculator()

    @pytest.mark.parametrize(
        ("n_col", "valid_unit", "valid_tarif", "valid_id"),
        [
            (30, UnitType.BOTTLE, TarifType.FORFAIT, "Tarif 3"),
            (96, UnitType.BOTTLE, TarifType.FORFAIT, "Tarif 8"),
            (97, UnitType.BOTTLE, TarifType.VARIABLE, "Tarif 9"),
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

    @pytest.mark.parametrize(
        ("n_col", "dpt", "cost"),
        [
            (30, "49", 22.95),
            (12, "79", 27.85),
            (24, "41", 35.92),
            (42, "95", 47.17),
            (64, "21", 57.99),
            (90, "01", 87.39),
            (66, "90", 86.66),
        ],
    )
    def test_compute_cost_forfait(self, n_col, dpt, cost):
        cost = self.cost_calc.compute_cost(
            expedition=SingleRefExpedition(n_bottles=n_col), department=dpt
        )
        assert cost == cost

    # unit_cost is the sum of the prices for all departments (and relivraison) for given number of bottles
    @pytest.mark.parametrize(
        ("n_col", "dpt", "unit_cost"), [(300, "49", 0.37), (540, "75", 0.68)]
    )
    def test_compute_cost_variable(self, n_col, dpt, unit_cost):
        cost = self.cost_calc.compute_cost(
            expedition=SingleRefExpedition(n_bottles=n_col),
            department=dpt,
        )
        assert cost == round(unit_cost * n_col, 2)
