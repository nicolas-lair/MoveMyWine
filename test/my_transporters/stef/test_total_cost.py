from src.my_transporters.stef.cost import StefTotalCost
from src.cost_calculator.expedition import MultiRefExpedition, SingleRefExpedition
from src.constant import BOTTLE, Package


class TestTotalCost:
    cost_calculator = StefTotalCost

    # def test_init(self):
    #     assert len(self.cost_calculator) == 3
    #     assert isinstance(self.cost_calculator.gnr_modulator, ModulatorFromIndicator)
    #     assert self.cost_calculator[CostType.ByBottle].gas_modulated
    #     assert self.cost_calculator[CostType.Expedition].gas_modulated
    #     assert not self.cost_calculator[CostType.Security].gas_modulated

    def test_compute_cost(self):
        exp = SingleRefExpedition(n_bottles=30, bottle_type=BOTTLE, package=Package())
        dep = "75"
        assert (
            self.cost_calculator.compute_cost(
                cold_factor=300, gnr_factor=1.0, expedition=exp, department=dep
            )
            == 43.14 + 0.7
        )
        assert (
            self.cost_calculator.compute_cost(
                cold_factor=300, gnr_factor=1.45, expedition=exp, department=dep
            )
            == 49.02
        )
        assert (
            self.cost_calculator.compute_cost(
                cold_factor=315, gnr_factor=1.0, expedition=exp, department=dep
            )
            == 44.06
        )
        assert (
            self.cost_calculator.compute_cost(
                cold_factor=315, gnr_factor=1.45, expedition=exp, department=dep
            )
            == 49.23
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
        ) == round(56.31 + 0.7, 2)
        assert (
            self.cost_calculator.compute_cost(
                cold_factor=300, gnr_factor=1.4, expedition=exp, department=dep
            )
            == 63.2
        )
        assert self.cost_calculator.compute_cost(
            cold_factor=315, gnr_factor=1.0, expedition=exp, department=dep
        ) == round(56.31 * 1.005 + 0.7, 2)
        assert self.cost_calculator.compute_cost(
            cold_factor=315, gnr_factor=1.4, expedition=exp, department=dep
        ) == round(56.31 * (1 + 0.11 + 0.005) + 0.7, 2)
