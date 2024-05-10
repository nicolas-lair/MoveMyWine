from src.cost_calculator.monthly_cost import MonthlyCostCalculator


class TestMonthlyCost:
    billing_cost = 25
    n_expedition_by_month = 7
    cost_without_gas_mod = MonthlyCostCalculator(
        gas_modulated=False, name="no_mod", billing_cost=billing_cost
    )

    def test_cost_value_without_gas_mod(self):
        assert self.cost_without_gas_mod.compute_cost(
            n_expedition_by_month=self.n_expedition_by_month
        ) == round(self.billing_cost / self.n_expedition_by_month, 2)

    def test_name(self):
        assert self.cost_without_gas_mod.name == "no_mod"
