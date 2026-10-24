import pytest

from src.cost_calculator import CostByPaletCalculator, SingleRefExpedition


@pytest.mark.parametrize(
    ("n_bottles", "cost"),
    [
        (546, 10.0),  # 671.6 kg + 25 kg palette -> 1 palette
        (552, 20.0),  # 679.0 kg + 25 kg palette -> 2 palettes
    ],
)
def test_cost_by_palet(n_bottles, cost):
    calc = CostByPaletCalculator(cost_by_palet=10.0, max_palet_weight=700)
    assert calc.compute_cost(SingleRefExpedition(n_bottles=n_bottles)) == cost
