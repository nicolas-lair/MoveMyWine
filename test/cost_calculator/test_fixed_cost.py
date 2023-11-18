from srcv2.cost_calculator.fixed_cost_by_expedition import FixedCostByExpe


class TestFixedCostByExpedition:
    cost = {"security_cost": 0.1, "expe_cost": 0.5}
    gas_factor = 2
    fixed_cost_with_gas_mod = FixedCostByExpe(gas_modulated=True, name="fixed_with_gas_modul", **cost)
    fixed_cost_without_gas_mod = FixedCostByExpe(gas_modulated=False, name="fixed_without_gas_modul", **cost)

    def test_cost_value_without_gas_mod(self):
        assert self.fixed_cost_without_gas_mod.compute_cost() == sum(self.cost.values())

    def test_cost_value_with_gas_mod(self):
        assert self.fixed_cost_with_gas_mod.compute_cost(gas_factor=2) == sum(self.cost.values()) * self.gas_factor
