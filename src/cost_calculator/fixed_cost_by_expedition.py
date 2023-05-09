class FixedCostByExpeditionCalculator:
    def __init__(self, **kwargs):
        self.fixed_cost_by_expedition = kwargs

    @property
    def total_cost(self) -> float:
        total_cost = sum(self.fixed_cost_by_expedition.values())
        return total_cost

