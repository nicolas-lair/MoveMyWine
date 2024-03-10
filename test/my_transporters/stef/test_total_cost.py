from srcv2.my_transporters.stef.cost import StefTotalCost
from srcv2.cost_calculator.gas_modulator import GasModulatorFromPrice
from srcv2.cost_calculator.constant import CostType
from srcv2.cost_calculator.expedition import MultiRefExpedition, SingleRefExpedition
from srcv2.constant import BOTTLE, Package


class TestTotalCost:
    cost_calculator = StefTotalCost()

    def test_init(self):
        assert len(self.cost_calculator) == 3
        assert isinstance(self.cost_calculator.gasModulator, GasModulatorFromPrice)
        assert self.cost_calculator[CostType.ByBottle].gas_modulated
        assert self.cost_calculator[CostType.Expedition].gas_modulated
        assert not self.cost_calculator[CostType.Security].gas_modulated

    def test_compute_cost(self):
        exp = SingleRefExpedition(n_bottles=30, bottle_type=BOTTLE, package=Package())
        dep = "75"
        assert (
            self.cost_calculator.compute_cost(
                gas_price=1.0, expedition=exp, department=dep
            )
            == 43.14 + 0.7
        )
        assert (
            self.cost_calculator.compute_cost(
                gas_price=1.45, expedition=exp, department=dep
            )
            == 49.02
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
            gas_price=1.0, expedition=exp, department=dep
        ) == round(56.31 + 0.7, 2)
        assert (
            self.cost_calculator.compute_cost(
                gas_price=1.4, expedition=exp, department=dep
            )
            == 63.2
        )
