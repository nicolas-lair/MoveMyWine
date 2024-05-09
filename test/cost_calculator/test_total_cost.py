from src.cost_calculator import (
    CostCollectionCalculator,
    CostType,
    FixedCostByExpe,
    MonthlyCostCalculator,
    CostByPackageCalculator,
    ExtraPackageCost,
    SingleRefExpedition,
    TotalCostCalculator,
    ModulatedCostCollection,
)


class TestTotalCost:
    total_cost = TotalCostCalculator(
        cost_collection=CostCollectionCalculator(
            {
                CostType.ByPackage: CostByPackageCalculator(
                    costs_by_package={"base_cost": 2},
                    extra_package_costs=ExtraPackageCost(
                        extra_package_cost=1,
                        max_free_package=3,
                        multi_package_max_fee=3.5,
                    ),
                ),
                CostType.Expedition: FixedCostByExpe(security=0.3, expedition=0.7),
                CostType.Monthly: MonthlyCostCalculator(billing_cost=15),
            }
        ),
        cost_modulator={
            CostType.GNRMod: ModulatedCostCollection(
                modulated_cost=[CostType.ByPackage, CostType.Expedition],
                modulator_arg_name="gas_factor",
            )
        },
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
