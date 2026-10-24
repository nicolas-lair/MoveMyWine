from typing import Any

import requests

DEFAULT_BASE_URL = "https://app.baqio.com/api/v1"
MAX_VARIANT_PAGES = 20


class BaqioError(Exception):
    pass


class BaqioAuthError(BaqioError):
    pass


class BaqioUnavailableError(BaqioError):
    pass


RECENT_ORDERS_PARAMS = [
    ("q[state_in][]", "pending"),
    ("q[state_in][]", "validated"),
    ("q[s]", "created_at desc"),
]


def build_search_params(text: str) -> list[tuple[str, str]]:
    return [*RECENT_ORDERS_PARAMS, ("q[name_or_customer_name_cont]", text)]


class BaqioClient:
    def __init__(
        self,
        user: str,
        password: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 15.0,
    ):
        self.user = user
        self.password = password
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get(
        self,
        path: str,
        params: list[tuple[str, str]] | None = None,
        allow_404: bool = False,
    ) -> Any:
        try:
            response = requests.get(
                f"{self.base_url}/{path}",
                params=params,
                auth=(self.user, self.password),
                headers={"Accept": "application/json"},
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise BaqioUnavailableError(f"Baqio unreachable: {e}") from e

        status = response.status_code
        if status in (401, 403):
            raise BaqioAuthError(f"Baqio authentication failed (HTTP {status})")
        if status == 404 and allow_404:
            return None
        if status >= 400:
            raise BaqioUnavailableError(f"Baqio request failed (HTTP {status})")
        try:
            return response.json()
        except ValueError as e:
            raise BaqioUnavailableError("Baqio returned invalid JSON") from e

    def recent_orders(self) -> list[dict]:
        """First page only: the 50 most recent uninvoiced orders."""
        return self._get("orders", params=RECENT_ORDERS_PARAMS)

    def search_orders(self, text: str) -> list[dict]:
        """First page only, for orders outside the preloaded ones."""
        return self._get("orders", params=build_search_params(text))

    def all_product_variants(self) -> dict[int, dict]:
        variants: dict[int, dict] = {}
        for page in range(1, MAX_VARIANT_PAGES + 1):
            body = self._get("product_variants", params=[("page", str(page))])
            if not body:
                break
            variants.update({variant["id"]: variant for variant in body})
        return variants

    def get_product_variant(self, variant_id: int) -> dict | None:
        return self._get(f"product_variants/{variant_id}", allow_404=True)
