from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

BOTTLE_ML = 750
MAGNUM_ML = 1500


@dataclass(frozen=True)
class IgnoredLine:
    description: str
    quantity: float


@dataclass(frozen=True)
class BaqioOrder:
    id: int
    name: str
    customer: str
    created_at: datetime
    bottles: int
    magnums: int
    zip: str | None
    city: str | None
    country: str | None
    ignored_lines: tuple[IgnoredLine, ...]

    @property
    def bottle_equivalent(self) -> int:
        return self.bottles + 2 * self.magnums


def variant_ids(raw: dict) -> set[int]:
    return {
        line["product_variant_id"]
        for line in raw["order_lines_not_deleted"]
        if line.get("product_variant_id") is not None
    }


def _address(raw: dict) -> dict:
    customer = raw.get("customer") or {}
    address = customer.get("shipping_information") or {}
    if address.get("use_billing_address"):
        address = customer.get("billing_information") or {}
    return address


def _line_description(line: dict) -> str:
    parts = [line.get("name"), line.get("description")]
    return " — ".join(part for part in parts if part)


def _format_ml(variant: dict | None) -> int | None:
    size = (variant or {}).get("product_size") or {}
    if size.get("kind") != "bottle":
        return None
    return size.get("milliliters")


def parse_order(raw: dict, variants: Mapping[int, dict | None]) -> BaqioOrder:
    bottles = magnums = 0
    ignored = []
    for line in raw["order_lines_not_deleted"]:
        if line.get("quantity") in (None, ""):
            ignored.append(IgnoredLine(_line_description(line), 0.0))
            continue
        quantity = float(line["quantity"])
        milliliters = _format_ml(variants.get(line.get("product_variant_id")))
        if quantity.is_integer() and milliliters == BOTTLE_ML:
            bottles += int(quantity)
        elif quantity.is_integer() and milliliters == MAGNUM_ML:
            magnums += int(quantity)
        else:
            ignored.append(IgnoredLine(_line_description(line), quantity))

    address = _address(raw)
    return BaqioOrder(
        id=raw["id"],
        name=raw["name"],
        customer=(raw.get("customer") or {}).get("name") or "",
        created_at=datetime.fromisoformat(raw["created_at"]),
        bottles=bottles,
        magnums=magnums,
        zip=address.get("zip"),
        city=address.get("city"),
        country=address.get("country_code"),
        ignored_lines=tuple(ignored),
    )


def order_label(raw: dict) -> str:
    customer = (raw.get("customer") or {}).get("name")
    city = _address(raw).get("city")
    created_at = datetime.fromisoformat(raw["created_at"])
    bottles = int(float(raw.get("bottle_quantity") or 0))
    parts = [raw["name"], customer, city, created_at.strftime("%d/%m")]
    return " · ".join(part for part in parts if part) + f" · {bottles} btl"


def split_cost(total: float, orders: Sequence[BaqioOrder]) -> list[float]:
    total_equivalent = sum(order.bottle_equivalent for order in orders)
    if total_equivalent == 0:
        raise ValueError("Cannot split a cost over orders without bottles")
    shares = [
        round(total * order.bottle_equivalent / total_equivalent, 2)
        for order in orders[:-1]
    ]
    shares.append(round(total - sum(shares), 2))
    return shares
