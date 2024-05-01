from src.cost_calculator import (
    TotalCostCalculator,
    CostType,
    FixedCostByExpe,
    MonthlyCostCalculator,
    CostByPackageCalculator,
    ExtraPackageCost,
    SingleRefExpedition,
)


class TestTotalCost:
    total_cost = TotalCostCalculator(
        {
            CostType.ByPackage: CostByPackageCalculator(
                gas_modulated=True,
                extra_package_costs=ExtraPackageCost(
                    extra_package_cost=1, max_free_package=3, multi_package_max_fee=3.5
                ),
                costs_by_package={"base_cost": 2},
            ),
            CostType.Expedition: FixedCostByExpe(
                gas_modulated=True, security=0.3, expedition=0.7
            ),
            CostType.Monthly: MonthlyCostCalculator(
                gas_modulated=False, billing_cost=15
            ),
        }
    )

    def test_total_cost_no_package(self):
        assert (
            self.total_cost.compute_cost(
                gas_factor=2,
                expedition=SingleRefExpedition(n_bottles=0),
                n_expedition_by_month=2,
            )
            == 0
        )

    def test_total_cost_one_package(self):
        assert (
            self.total_cost.compute_cost(
                gas_factor=2,
                expedition=SingleRefExpedition(n_bottles=6),
                n_expedition_by_month=2,
            )
            == 2 * (2 + 1) + 15 / 2
        )

    def test_total_cost_four_package(self):
        assert (
            self.total_cost.compute_cost(
                gas_factor=2,
                expedition=SingleRefExpedition(n_bottles=24),
                n_expedition_by_month=2,
            )
            == 2 * (4 * 2 + 1 + 1) + 15 / 2
        )

    def test_total_cost_fourty_package(self):
        assert (
            self.total_cost.compute_cost(
                gas_factor=2,
                expedition=SingleRefExpedition(n_bottles=240),
                n_expedition_by_month=2,
            )
            == 2 * (40 * 2 + 1 + 3.5) + 15 / 2
        )
