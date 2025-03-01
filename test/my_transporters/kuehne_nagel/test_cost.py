import pandas as pd
import pytest

from src.cost_calculator.expedition import SingleRefExpedition
from src.my_transporters.stef.cost import StefCostByBottleCalculator
from src.constant import UnitType, TarifType


class TestCostByBottle:
    cost_calc = StefCostByBottleCalculator()

    def test_get_tarif_unit(self):
        assert self.cost_calc._get_tarif_unit(30) == UnitType.BOTTLE
        assert self.cost_calc._get_tarif_unit(198) == UnitType.BOTTLE
        with pytest.raises(NotImplementedError):
            _ = self.cost_calc._get_tarif_unit(199)

    def test_get_tarif_conditions(self):
        t_unit, t_type, t_id = self.cost_calc.get_tarif_conditions(30)
        assert t_unit == UnitType.BOTTLE
        assert t_type == TarifType.FORFAIT
        assert t_id == "Tarif 1"

        t_unit, t_type, t_id = self.cost_calc.get_tarif_conditions(78)
        assert t_unit == UnitType.BOTTLE
        assert t_type == TarifType.FORFAIT
        assert t_id == "Tarif 2"

        t_unit, t_type, t_id = self.cost_calc.get_tarif_conditions(79)
        assert t_unit == UnitType.BOTTLE
        assert t_type == TarifType.VARIABLE
        assert t_id == "Tarif 3"

        with pytest.raises(NotImplementedError):
            _ = self.cost_calc._get_tarif_unit(199)

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
