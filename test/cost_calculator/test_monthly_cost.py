from srcv2.cost_calculator.monthly_cost import MonthlyCostCalculator
from srcv2.cost_calculator.constant import CostType


class TestMonthlyCost:
    billing_cost = 25
    gas_factor = 2
    n_expedition_by_month = 7
    cost_with_gas_mod = MonthlyCostCalculator(
        gas_modulated=True, billing_cost=billing_cost
    )
    cost_without_gas_mod = MonthlyCostCalculator(
        gas_modulated=False, name="no_mod", billing_cost=billing_cost
    )

    def test_cost_value_without_gas_mod(self):
        assert (
            self.cost_without_gas_mod.compute_cost(
                n_expedition_by_month=self.n_expedition_by_month
            )
            == self.billing_cost / self.n_expedition_by_month
        )

    def test_cost_value_with_gas_mod(self):
        assert (
            self.cost_with_gas_mod.compute_cost(
                n_expedition_by_month=self.n_expedition_by_month, gas_factor=2
            )
            == self.billing_cost / self.n_expedition_by_month * self.gas_factor
        )

    def test_name(self):
        assert self.cost_with_gas_mod.name == CostType.Monthly
        assert self.cost_without_gas_mod.name == "no_mod"
