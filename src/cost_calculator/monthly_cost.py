from src.constant import N_EXPEDITION


class MonthlyCostCalculator:
    def __init__(self, **kwargs):
        self.monthly_cost = kwargs

    def get_total_cost(self, n_expedition_by_month: int = N_EXPEDITION) -> float:
        total_cost = sum(self.monthly_cost.values()) / n_expedition_by_month
        return total_cost
