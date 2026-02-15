import pytest

from src.constant import BOTTLE, Package
from src.cost_calculator.expedition import MultiRefExpedition, SingleRefExpedition
from src.my_transporters.geodis.cost import GeodisTotalCost


class TestTotalCost:
    cost_calculator = GeodisTotalCost

    @pytest.mark.parametrize(
        ("gnr_factor", "true_cost"),
        [
            (0, round((42.88 + 2.2), 2)),
            (10, round((42.88 + 2.2) * 1.1, 2)),
        ],
    )
    def test_single_exp_computation(self, gnr_factor, true_cost):
        exp = SingleRefExpedition(n_bottles=30, bottle_type=BOTTLE, package=Package())
        dep = "75"
        assert (
            self.cost_calculator.compute_cost(
                gnr_factor=gnr_factor,
                expedition=exp,
                department=dep,
            )
            == true_cost
        )

    @pytest.mark.parametrize(
        ("gnr_factor", "true_cost"),
        [
            (0, round((57.99 + 2.2), 2)),
            (10, round((57.99 + 2.2) * 1.1, 2)),
        ],
    )
    def test_multi_exp_computation(self, gnr_factor, true_cost):
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
                gnr_factor=gnr_factor,
                expedition=exp,
                department=dep,
            )
            == true_cost
        )
