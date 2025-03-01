import pytest

from src.my_transporters.kuehne_nagel.cost import KNGTotalCost
from src.cost_calculator.expedition import MultiRefExpedition, SingleRefExpedition
from src.constant import BOTTLE, Package


class TestTotalCost:
    cost_calculator = KNGTotalCost

    @pytest.mark.parametrize(("cold_factor", "gnr_factor", "true_cost"), [])
    def test_single_exp_computation(self, cold_factor, gnr_factor, true_cost):
        exp = SingleRefExpedition(n_bottles=30, bottle_type=BOTTLE, package=Package())
        dep = "75"
        assert (
            self.cost_calculator.compute_cost(
                cold_factor=cold_factor,
                gnr_factor=gnr_factor,
                expedition=exp,
                department=dep,
            )
            == true_cost
        )

    @pytest.mark.parametrize(("cold_factor", "gnr_factor", "true_cost"), [])
    def test_multi_exp_computation(self, cold_factor, gnr_factor, true_cost):
        exp = MultiRefExpedition(
            [
                SingleRefExpedition(
                    n_bottles=30, bottle_type=BOTTLE, package=Package()
                ),
                SingleRefExpedition(
                    n_bottles=24, bottle_type=BOTTLE, package=Package()
                ),
            ]
        )
        dep = "69"
        assert (
            self.cost_calculator.compute_cost(
                cold_factor=cold_factor,
                gnr_factor=gnr_factor,
                expedition=exp,
                department=dep,
            )
            == true_cost
        )
