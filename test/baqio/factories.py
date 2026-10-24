"""Builders of anonymised Baqio payloads (real structure, invented data)."""


def make_line(
    variant_id, quantity, name="Cuvée", description="Bouteille (75 cl)"
) -> dict:
    return {
        "product_variant_id": variant_id,
        "quantity": f"{float(quantity)}" if not isinstance(quantity, str) else quantity,
        "name": name,
        "description": description,
    }


def make_order(
    id=1,
    name="#1",
    customer="Client A",
    lines=(),
    zip="33000",
    city="BORDEAUX",
    country="FR",
    use_billing_address=False,
    created_at="2026-09-21T13:25:41.634+02:00",
    bottle_quantity="0.0",
) -> dict:
    address = {"zip": zip, "city": city, "country_code": country}
    empty = {"zip": None, "city": None, "country_code": None}
    if use_billing_address:
        shipping = {**empty, "use_billing_address": True}
        billing = address
    else:
        shipping = {**address, "use_billing_address": False}
        billing = empty
    return {
        "id": id,
        "name": name,
        "created_at": created_at,
        "state": "pending",
        "bottle_quantity": bottle_quantity,
        "customer": {
            "name": customer,
            "shipping_information": shipping,
            "billing_information": billing,
        },
        "order_lines_not_deleted": list(lines),
    }


def make_variant(id, milliliters=750, kind="bottle") -> dict:
    return {
        "id": id,
        "product_size": {
            "id": id * 10,
            "name": f"Format {milliliters} ml",
            "milliliters": milliliters,
            "kind": kind,
        },
    }
