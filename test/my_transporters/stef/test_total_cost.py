import pytest

from src.constant import BOTTLE, Package
from src.cost_calculator.expedition import MultiRefExpedition, SingleRefExpedition
from src.my_transporters.stef.cost import StefTotalCost


class TestTotalCost:
    cost_calculator = StefTotalCost

    @pytest.mark.parametrize(
        ("cold_factor", "gnr_factor", "true_cost"),
        [
            (300, 1.0, round((41.68 + 5.41) + 0.7 + 1.0, 2)),
            (300, 1.45, round((41.68 + 5.41) * 1.12 + 0.7 + 1.0, 2)),
            (315, 1.0, round((41.68 + 5.41) * 1.005 + 0.7 + 1.0, 2)),
            (315, 1.45, 54.68),
        ],
    )
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

    @pytest.mark.parametrize(
        ("cold_factor", "gnr_factor", "true_cost"),
        [
            (300, 1.0, round((56.14 + 5.41) + 0.7 + 1.0, 2)),
            (300, 1.4, round((56.14 + 5.41) * 1.11 + 0.7 + 1.0, 2)),
            (315, 1.0, round((56.14 + 5.41) * 1.005 + 0.7 + 1.0, 2)),
            (315, 1.4, 70.33),
        ],
    )
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
