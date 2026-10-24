import pytest

from src.constant import BOTTLE, Package
from src.cost_calculator.expedition import MultiRefExpedition, SingleRefExpedition
from src.my_transporters.geodis.cost import (
    GeodisMessagerieTotalCost,
    GeodisPaletteTotalCost,
)


class TestTotalCost:
    cost_calculator = GeodisMessagerieTotalCost

    @pytest.mark.parametrize(
        ("gnr_factor", "true_cost"),
        [
            (0, round((37.25 + 2.15 + 6.6) + 5, 2)),
            (10, round((37.25 + 2.15 + 6.6) * 1.1 + 5, 2)),
        ],
    )
    def test_single_exp_computation(self, gnr_factor, true_cost):
        exp = SingleRefExpedition(n_bottles=30, bottle_type=BOTTLE, package=Package())
        postal_code = "75001"
        dep = postal_code[:2]
        assert (
            self.cost_calculator.compute_cost(
                gnr_factor=gnr_factor,
                postal_code=postal_code,
                expedition=exp,
                department=dep,
            )
            == true_cost
        )

    @pytest.mark.parametrize(
        ("gnr_factor", "true_cost"),
        [
            (0, round((69.3 + 2.15) + 5, 2)),
            (10, round((69.3 + 2.15) * 1.1 + 5, 2)),
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
        postal_code = "90001"
        dep = postal_code[:2]
        assert (
            self.cost_calculator.compute_cost(
                gnr_factor=gnr_factor,
                postal_code=postal_code,
                expedition=exp,
                department=dep,
            )
            == true_cost
        )


class TestPaletteTotalCost:
    cost_calculator = GeodisPaletteTotalCost

    @pytest.mark.parametrize(
        ("gnr_factor", "true_cost"),
        [
            (0, round((130.26 + 2.15 + 6.6) + 10, 2)),
            (10, round((130.26 + 2.15 + 6.6) * 1.1 + 10, 2)),
        ],
    )
    def test_single_exp_computation(self, gnr_factor, true_cost):
        exp = SingleRefExpedition(n_bottles=30, bottle_type=BOTTLE, package=Package())
        assert (
            self.cost_calculator.compute_cost(
                gnr_factor=gnr_factor,
                postal_code="75001",
                expedition=exp,
                department="75",
            )
            == true_cost
        )
