from src.cost_calculator import (
    BaseCostList,
    CostType,
    FixedCostByExpe,
    MonthlyCostCalculator,
    CostByPackageCalculator,
    ExtraPackageCost,
    SingleRefExpedition,
)


class TestCostCollectionCalc:
    cost_collection = BaseCostList(
        [
            CostByPackageCalculator(
                costs_by_package={"base_cost": 2},
                extra_package_costs=ExtraPackageCost(
                    extra_package_cost=1,
                    max_free_package=3,
                    multi_package_max_fee=3.5,
                ),
            ),
            FixedCostByExpe(security=0.3, expedition=0.7),
            MonthlyCostCalculator(billing_cost=15),
        ]
    )

    def test_total_cost_no_package(self):
        cost_dict = self.cost_collection.compute_cost(
            expedition=SingleRefExpedition(n_bottles=0),
            n_expedition_by_month=2,
        )
        assert isinstance(cost_dict, dict)
        assert len(cost_dict.keys()) == len(self.cost_collection)
        assert all([c == 0 for c in cost_dict.values()])

    def test_total_cost_one_package(self):
        cost_dict = self.cost_collection.compute_cost(
            expedition=SingleRefExpedition(n_bottles=6),
            n_expedition_by_month=2,
        )
        assert isinstance(cost_dict, dict)
        assert len(cost_dict.keys()) == len(self.cost_collection)
        assert cost_dict.pop(CostType.ByPackage) == 2
        assert cost_dict.pop(CostType.Expedition) == 1
        assert cost_dict.pop(CostType.Monthly) == 7.5
        assert len(cost_dict) == 0

    def test_total_cost_four_package(self):
        cost_dict = self.cost_collection.compute_cost(
            expedition=SingleRefExpedition(n_bottles=24),
            n_expedition_by_month=2,
        )
        assert isinstance(cost_dict, dict)
        assert len(cost_dict.keys()) == len(self.cost_collection)
        assert cost_dict.pop(CostType.ByPackage) == 4 * 2 + 1
        assert cost_dict.pop(CostType.Expedition) == 1
        assert cost_dict.pop(CostType.Monthly) == 7.5
        assert len(cost_dict) == 0

    def test_total_cost_fourty_package(self):
        cost_dict = self.cost_collection.compute_cost(
            expedition=SingleRefExpedition(n_bottles=240),
            n_expedition_by_month=2,
        )
        assert isinstance(cost_dict, dict)
        assert len(cost_dict.keys()) == len(self.cost_collection)
        assert cost_dict.pop(CostType.ByPackage) == 40 * 2 + 3.5
        assert cost_dict.pop(CostType.Expedition) == 1
        assert cost_dict.pop(CostType.Monthly) == 7.5
        assert len(cost_dict) == 0
