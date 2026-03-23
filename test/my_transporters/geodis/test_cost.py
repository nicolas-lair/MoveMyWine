import pytest

from src.constant import TarifType, UnitType
from src.cost_calculator.expedition import SingleRefExpedition
from src.my_transporters.geodis.cost import CostByDestination, MyCostByBottleCalculator


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


class TestDestinationCost:
    cost_calc = CostByDestination()

    @pytest.mark.parametrize(
        ("value", "interval_list", "idx"),
        [
            (0, [1, 3], 0),
            (1, [1, 3], 0),
            (2, [1, 3], 1),
            (3, [1, 3], 1),
            (4, [1, 3], 2),
        ],
    )
    def test_get_index_from_interval(self, value, interval_list, idx):
        assert self.cost_calc._get_index_from_interval(value, interval_list) == idx

    @pytest.mark.parametrize(
        ("n_col", "postal_code", "dpt", "cost"),
        [
            (12, "01001", "01", 0),
            (12, "75001", "75", 3.4),
            (36, "44100", "44", 6.8),
            (120, "69009", "69", 10.4),
            (36, "89100", "89", 4.1),
        ],
    )
    def test_cost(self, n_col, postal_code, dpt, cost):
        expedition = SingleRefExpedition(n_bottles=n_col)
        assert (
            self.cost_calc.compute_cost(
                expedition, postal_code=postal_code, department=dpt
            )
            == cost
        )
