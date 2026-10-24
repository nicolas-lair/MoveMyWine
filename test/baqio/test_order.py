import pytest

from src.baqio.order import (
    BaqioOrder,
    IgnoredLine,
    order_label,
    parse_order,
    split_cost,
    variant_ids,
)
from test.baqio.factories import make_line, make_order, make_variant


def _order_with_equivalent(bottles: int, magnums: int = 0) -> BaqioOrder:
    lines = [make_line(1, bottles)]
    variants = {1: make_variant(1, 750)}
    if magnums:
        lines.append(make_line(2, magnums))
        variants[2] = make_variant(2, 1500)
    return parse_order(make_order(lines=lines), variants)


def test_classifies_bottles_and_magnums():
    raw = make_order(lines=[make_line(1, 24), make_line(2, 6)])
    variants = {1: make_variant(1, 750), 2: make_variant(2, 1500)}

    order = parse_order(raw, variants)

    assert order.bottles == 24
    assert order.magnums == 6
    assert order.bottle_equivalent == 36
    assert order.ignored_lines == ()


def test_ignores_other_formats():
    raw = make_order(
        lines=[
            make_line(1, 2, name="Vrac", description="Cuve"),
            make_line(2, 3, name="Demi", description="Demi-bouteille"),
            make_line(3, 4, name="Fontaine", description="BIB 3 l"),
            make_line(None, 5, name="Livraison", description="Transport"),
            make_line(99, 6, name="Inconnu", description="Variante absente"),
        ]
    )
    variants = {
        1: make_variant(1, 13.56, kind="bulk"),
        2: make_variant(2, 375, kind="bottle"),
        3: make_variant(3, 3000, kind="bib"),
        99: None,
    }

    order = parse_order(raw, variants)

    assert order.bottles == 0
    assert order.magnums == 0
    assert order.ignored_lines == (
        IgnoredLine("Vrac — Cuve", 2.0),
        IgnoredLine("Demi — Demi-bouteille", 3.0),
        IgnoredLine("Fontaine — BIB 3 l", 4.0),
        IgnoredLine("Livraison — Transport", 5.0),
        IgnoredLine("Inconnu — Variante absente", 6.0),
    )


def test_ignores_non_integer_quantity():
    raw = make_order(lines=[make_line(1, "13.5", name="Cuvée", description="Reste")])

    order = parse_order(raw, {1: make_variant(1, 750)})

    assert order.bottles == 0
    assert order.magnums == 0
    assert order.ignored_lines == (IgnoredLine("Cuvée — Reste", 13.5),)


def test_shipping_address():
    raw = make_order(zip="69001", city="LYON", country="FR")

    order = parse_order(raw, {})

    assert (order.zip, order.city, order.country) == ("69001", "LYON", "FR")


def test_billing_address_fallback():
    raw = make_order(zip="75002", city="PARIS", country="FR", use_billing_address=True)
    assert raw["customer"]["shipping_information"]["zip"] is None

    order = parse_order(raw, {})

    assert (order.zip, order.city, order.country) == ("75002", "PARIS", "FR")


def test_order_metadata():
    raw = make_order(
        id=7,
        name="#9001",
        customer="Cave Exemple",
        created_at="2026-09-23T10:00:00+02:00",
    )

    order = parse_order(raw, {})

    assert order.id == 7
    assert order.name == "#9001"
    assert order.customer == "Cave Exemple"
    assert (order.created_at.year, order.created_at.month, order.created_at.day) == (
        2026,
        9,
        23,
    )


def test_missing_customer_or_address():
    no_customer = make_order()
    no_customer["customer"] = None
    order = parse_order(no_customer, {})
    assert order.customer == ""
    assert order.zip is order.city is order.country is None

    no_address = make_order()
    no_address["customer"]["shipping_information"] = None
    no_address["customer"]["billing_information"] = None
    order = parse_order(no_address, {})
    assert order.customer == "Client A"
    assert order.zip is order.city is order.country is None


def test_variant_ids():
    raw = make_order(
        lines=[make_line(1, 2), make_line(2, 3), make_line(1, 4), make_line(None, 1)]
    )

    assert variant_ids(raw) == {1, 2}


def test_order_label():
    raw = make_order(
        name="#9001",
        customer="Cave Exemple",
        city="BORDEAUX",
        created_at="2026-09-23T10:00:00+02:00",
        bottle_quantity="36.0",
    )

    assert order_label(raw) == "#9001 · Cave Exemple · BORDEAUX · 23/09 · 36 btl"


def test_split_cost_prorata():
    orders = [
        _order_with_equivalent(36),
        _order_with_equivalent(0, magnums=6),
        _order_with_equivalent(24),
    ]
    assert [o.bottle_equivalent for o in orders] == [36, 12, 24]

    shares = split_cost(100.0, orders)

    assert shares == [50.0, 16.67, 33.33]
    assert sum(shares) == pytest.approx(100.0, abs=1e-9)


def test_split_cost_rounding_absorbed_by_last():
    orders = [_order_with_equivalent(1) for _ in range(3)]

    assert split_cost(10.0, orders) == [3.33, 3.33, 3.34]


def test_split_cost_single_order():
    assert split_cost(42.5, [_order_with_equivalent(12)]) == [42.5]


def test_split_cost_zero_equivalent_raises():
    empty = parse_order(make_order(), {})
    assert empty.bottle_equivalent == 0

    with pytest.raises(ValueError):
        split_cost(10.0, [empty])


@pytest.mark.parametrize("quantity", [None, "36.0"])
def test_order_label_tolerates_missing_bottle_quantity(quantity):
    raw = make_order(name="#9001", customer="Cave Exemple", bottle_quantity=quantity)
    if quantity is None:
        assert order_label(raw).endswith(" · 0 btl")
        del raw["bottle_quantity"]
        assert order_label(raw).endswith(" · 0 btl")
    else:
        assert order_label(raw).endswith(" · 36 btl")


@pytest.mark.parametrize("quantity", [None, ""])
def test_line_without_quantity_is_ignored(quantity):
    line = make_line(1, 1)
    line["quantity"] = quantity
    raw = make_order(lines=[line, make_line(1, 6)])

    order = parse_order(raw, {1: make_variant(1, 750)})

    assert order.bottles == 6
    assert len(order.ignored_lines) == 1
    assert order.ignored_lines[0].quantity == 0.0
