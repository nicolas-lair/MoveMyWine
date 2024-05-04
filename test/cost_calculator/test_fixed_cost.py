from src.cost_calculator.fixed_cost_by_expedition import FixedCostByExpe


class TestFixedCostByExpedition:
    cost = {"security_cost": 0.1, "expe_cost": 0.5}
    fixed_cost_without_gas_mod = FixedCostByExpe(name="fixed_without_gas_modul", **cost)

    def test_cost_value_without_gas_mod(self):
        assert self.fixed_cost_without_gas_mod.compute_cost() == sum(self.cost.values())

    def test_name(self):
        assert self.fixed_cost_without_gas_mod.name == "fixed_without_gas_modul"
