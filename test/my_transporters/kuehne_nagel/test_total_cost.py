from src.my_transporters.stef.cost import StefTotalCost
from src.cost_calculator.expedition import MultiRefExpedition, SingleRefExpedition
from src.constant import BOTTLE, Package


class TestTotalCost:
    cost_calculator = StefTotalCost

    def test_compute_cost(self):
        exp = SingleRefExpedition(n_bottles=30, bottle_type=BOTTLE, package=Package())
        dep = "75"
        assert self.cost_calculator.compute_cost(
            cold_factor=300, gnr_factor=1.0, expedition=exp, department=dep
        ) == round((39.46 + 5.41) + 0.7, 2)
        assert self.cost_calculator.compute_cost(
            cold_factor=300, gnr_factor=1.45, expedition=exp, department=dep
        ) == round((39.46 + 5.41) * 1.12 + 0.7, 2)
        assert self.cost_calculator.compute_cost(
            cold_factor=315, gnr_factor=1.0, expedition=exp, department=dep
        ) == round((39.46 + 5.41) * 1.005 + 0.7, 2)
        assert (
            self.cost_calculator.compute_cost(
                cold_factor=315, gnr_factor=1.45, expedition=exp, department=dep
            )
            == 51.17
        )

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
        assert self.cost_calculator.compute_cost(
            cold_factor=300, gnr_factor=1.0, expedition=exp, department=dep
        ) == round((53.15 + 5.41) + 0.7, 2)
        assert self.cost_calculator.compute_cost(
            cold_factor=300, gnr_factor=1.4, expedition=exp, department=dep
        ) == round((53.15 + 5.41) * 1.11 + 0.7, 2)
        assert self.cost_calculator.compute_cost(
            cold_factor=315, gnr_factor=1.0, expedition=exp, department=dep
        ) == round((53.15 + 5.41) * 1.005 + 0.7, 2)
        assert (
            self.cost_calculator.compute_cost(
                cold_factor=315, gnr_factor=1.4, expedition=exp, department=dep
            )
            == 65.99
        )
