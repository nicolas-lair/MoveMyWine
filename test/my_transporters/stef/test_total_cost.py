import pytest

from src.my_transporters.stef.cost import StefTotalCost
from src.cost_calculator.expedition import MultiRefExpedition, SingleRefExpedition
from src.constant import BOTTLE, Package


class TestTotalCost:
    cost_calculator = StefTotalCost

    @pytest.mark.parametrize(
        ("cold_factor", "gnr_factor", "true_cost"),
        [
            (300, 1.0, round((39.46 + 5.41) + 0.7, 2)),
            (300, 1.45, round((39.46 + 5.41) * 1.12 + 0.7, 2)),
            (315, 1.0, round((39.46 + 5.41) * 1.005 + 0.7, 2)),
            (315, 1.45, 51.17),
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
            (300, 1.0, round((53.15 + 5.41) + 0.7, 2)),
            (300, 1.4, round((53.15 + 5.41) * 1.11 + 0.7, 2)),
            (315, 1.0, round((53.15 + 5.41) * 1.005 + 0.7, 2)),
            (315, 1.4, 65.99),
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
