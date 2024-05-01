from src.cost_calculator.cost_by_package import (
    ExtraPackageCost,
    CostByPackageCalculator,
)
from src.cost_calculator.expedition import SingleRefExpedition
from src.cost_calculator.constant import CostType

free_extra_package_cost = ExtraPackageCost()
custom_extra_package_cost = ExtraPackageCost(
    extra_package_cost=1, max_free_package=3, multi_package_max_fee=3.5
)
base_package_cost = {"package_cost": 3}


class TestExtraPackageCost:
    def test_free_extra_package(self):
        assert free_extra_package_cost.compute_extra_cost(0) == 0
        assert free_extra_package_cost.compute_extra_cost(1) == 0
        assert free_extra_package_cost.compute_extra_cost(10) == 0

    def test_custom_extra_package_cost(self):
        assert custom_extra_package_cost.compute_extra_cost(1) == 0
        assert custom_extra_package_cost.compute_extra_cost(3) == 0
        assert custom_extra_package_cost.compute_extra_cost(4) == 1
        assert custom_extra_package_cost.compute_extra_cost(5) == 2
        assert custom_extra_package_cost.compute_extra_cost(10) == 3.5


class TestCostByPackageCalculator:
    no_cost = CostByPackageCalculator(
        gas_modulated=False, extra_package_costs=free_extra_package_cost, name="free"
    )
    no_base_cost = CostByPackageCalculator(
        gas_modulated=False, extra_package_costs=custom_extra_package_cost
    )
    cost_calc = CostByPackageCalculator(
        gas_modulated=True,
        costs_by_package=base_package_cost,
        extra_package_costs=custom_extra_package_cost,
    )

    def test_base_cost(self):
        assert self.cost_calc.base_cost_by_package == base_package_cost["package_cost"]
        assert self.no_cost.base_cost_by_package == 0

    def test_no_cost(self):
        assert (
            self.no_cost.compute_cost(expedition=SingleRefExpedition(n_bottles=6)) == 0
        )

    def test_no_base_cost(self):
        assert (
            self.no_base_cost.compute_cost(expedition=SingleRefExpedition(n_bottles=6))
            == 0
        )
        assert (
            self.no_base_cost.compute_cost(expedition=SingleRefExpedition(n_bottles=24))
            == 1
        )
        assert (
            self.no_base_cost.compute_cost(
                expedition=SingleRefExpedition(n_bottles=240)
            )
            == 3.5
        )

    def test_cost_without_gas_mod(self):
        self.cost_calc.gas_modulated = False
        assert (
            self.cost_calc.compute_cost(expedition=SingleRefExpedition(n_bottles=12))
            == 2 * base_package_cost["package_cost"]
        )
        assert (
            self.cost_calc.compute_cost(expedition=SingleRefExpedition(n_bottles=24))
            == 4 * base_package_cost["package_cost"] + 1
        )
        assert (
            self.cost_calc.compute_cost(expedition=SingleRefExpedition(n_bottles=240))
            == 40 * base_package_cost["package_cost"] + 3.5
        )

    def test_cost_with_gas_mod(self):
        self.cost_calc.gas_modulated = True
        assert self.cost_calc.compute_cost(
            gas_factor=2, expedition=SingleRefExpedition(n_bottles=12)
        ) == 2 * (2 * base_package_cost["package_cost"])
        assert self.cost_calc.compute_cost(
            gas_factor=2, expedition=SingleRefExpedition(n_bottles=24)
        ) == 2 * (4 * base_package_cost["package_cost"] + 1)
        assert self.cost_calc.compute_cost(
            gas_factor=2, expedition=SingleRefExpedition(n_bottles=240)
        ) == 2 * (40 * base_package_cost["package_cost"] + 3.5)

    def test_name(self):
        assert self.no_cost.name == "free"
        assert self.no_base_cost.name == CostType.ByPackage
