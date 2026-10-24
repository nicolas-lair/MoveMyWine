import pytest
import requests

from src.baqio import client as client_module
from src.baqio.client import (
    RECENT_ORDERS_PARAMS,
    BaqioAuthError,
    BaqioClient,
    BaqioUnavailableError,
)


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class FakeGet:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def __call__(self, url, params=None, auth=None, headers=None, timeout=None):
        self.calls.append(
            {
                "url": url,
                "params": params,
                "auth": auth,
                "headers": headers,
                "timeout": timeout,
            }
        )
        if self.error is not None:
            raise self.error
        return self.response


def install_fake(monkeypatch, status_code=200, payload=None, error=None):
    fake = FakeGet(FakeResponse(status_code, payload), error)
    monkeypatch.setattr("src.baqio.client.requests.get", fake)
    return fake


def test_recent_orders_params_constant():
    assert RECENT_ORDERS_PARAMS == [
        ("q[state_in][]", "pending"),
        ("q[state_in][]", "validated"),
        ("q[s]", "created_at desc"),
    ]


def test_recent_orders_request(monkeypatch):
    orders = [{"id": 1}, {"id": 2}]
    fake = install_fake(monkeypatch, payload=orders)

    result = BaqioClient("u", "p").recent_orders()

    assert result == orders
    assert len(fake.calls) == 1
    call = fake.calls[0]
    assert call["url"] == "https://app.baqio.com/api/v1/orders"
    assert call["params"] == RECENT_ORDERS_PARAMS
    assert not any("name_or_customer_name_cont" in key for key, _ in call["params"])
    assert call["auth"] == ("u", "p")
    assert call["headers"] == {"Accept": "application/json"}
    assert call["timeout"] is not None


def test_build_search_params():
    params = client_module.build_search_params("dupont")

    assert params == RECENT_ORDERS_PARAMS + [
        ("q[name_or_customer_name_cont]", "dupont")
    ]
    assert RECENT_ORDERS_PARAMS[-1] == ("q[s]", "created_at desc")  # not mutated


def test_search_orders_request(monkeypatch):
    orders = [{"id": 7}]
    fake = install_fake(monkeypatch, payload=orders)

    result = BaqioClient("u", "p").search_orders("#1234")

    assert result == orders
    assert len(fake.calls) == 1
    call = fake.calls[0]
    assert call["url"] == "https://app.baqio.com/api/v1/orders"
    assert call["params"] == RECENT_ORDERS_PARAMS + [
        ("q[name_or_customer_name_cont]", "#1234")
    ]
    assert call["auth"] == ("u", "p")
    assert call["headers"] == {"Accept": "application/json"}


@pytest.mark.parametrize(
    "status_code, exception",
    [(401, BaqioAuthError), (403, BaqioAuthError), (500, BaqioUnavailableError)],
)
def test_search_orders_errors(monkeypatch, status_code, exception):
    install_fake(monkeypatch, status_code=status_code)

    with pytest.raises(exception):
        BaqioClient("u", "p").search_orders("x")


def test_custom_base_url(monkeypatch):
    fake = install_fake(monkeypatch, payload=[])

    BaqioClient("u", "p", base_url="https://demo.baqio.com/api/v1").recent_orders()

    assert fake.calls[0]["url"] == "https://demo.baqio.com/api/v1/orders"


def test_get_product_variant(monkeypatch):
    variant = {"id": 222206, "name": "Cuvee"}
    fake = install_fake(monkeypatch, payload=variant)

    result = BaqioClient("u", "p").get_product_variant(222206)

    assert result == variant
    assert (
        fake.calls[0]["url"] == "https://app.baqio.com/api/v1/product_variants/222206"
    )
    assert fake.calls[0]["auth"] == ("u", "p")
    assert fake.calls[0]["timeout"] is not None


def test_get_product_variant_404_returns_none(monkeypatch):
    install_fake(monkeypatch, status_code=404, payload={})

    assert BaqioClient("u", "p").get_product_variant(1) is None


@pytest.mark.parametrize("status_code", [401, 403])
def test_auth_errors(monkeypatch, status_code):
    install_fake(monkeypatch, status_code=status_code, payload={})

    with pytest.raises(BaqioAuthError):
        BaqioClient("u", "p").recent_orders()


@pytest.mark.parametrize("status_code", [500, 503])
def test_server_error(monkeypatch, status_code):
    install_fake(monkeypatch, status_code=status_code, payload={})

    with pytest.raises(BaqioUnavailableError):
        BaqioClient("u", "p").recent_orders()


@pytest.mark.parametrize(
    "error",
    [
        requests.ConnectionError(),
        requests.Timeout(),
        requests.TooManyRedirects(),
        requests.exceptions.InvalidURL(),
    ],
)
def test_network_errors(monkeypatch, error):
    install_fake(monkeypatch, error=error)

    with pytest.raises(BaqioUnavailableError):
        BaqioClient("u", "p").recent_orders()


class BadJsonResponse(FakeResponse):
    def json(self):
        raise requests.exceptions.JSONDecodeError("x", "", 0)


@pytest.mark.parametrize(
    "call",
    [
        lambda client: client.recent_orders(),
        lambda client: client.get_product_variant(222206),
    ],
)
def test_invalid_json_raises_unavailable(monkeypatch, call):
    fake = FakeGet(BadJsonResponse(200))
    monkeypatch.setattr("src.baqio.client.requests.get", fake)

    with pytest.raises(BaqioUnavailableError):
        call(BaqioClient("u", "p"))


class PagedGet:
    """Fake requests.get serving one payload per `page` param (empty list after)."""

    def __init__(self, pages, status_code=200):
        self.pages = pages
        self.status_code = status_code
        self.calls = []

    def __call__(self, url, params=None, auth=None, headers=None, timeout=None):
        self.calls.append({"url": url, "params": params, "auth": auth})
        page = int(dict(params)["page"])
        payload = self.pages[page - 1] if page <= len(self.pages) else []
        return FakeResponse(self.status_code, payload)


def install_paged(monkeypatch, pages, status_code=200):
    fake = PagedGet(pages, status_code)
    monkeypatch.setattr("src.baqio.client.requests.get", fake)
    return fake


def test_max_variant_pages_constant():
    assert client_module.MAX_VARIANT_PAGES == 20


def test_all_product_variants_paginates_until_empty_page(monkeypatch):
    pages = [[{"id": 1}, {"id": 2}], [{"id": 3}]]
    fake = install_paged(monkeypatch, pages)

    result = BaqioClient("u", "p").all_product_variants()

    assert result == {1: {"id": 1}, 2: {"id": 2}, 3: {"id": 3}}
    assert [c["params"] for c in fake.calls] == [
        [("page", "1")],
        [("page", "2")],
        [("page", "3")],
    ]
    assert all(
        c["url"] == "https://app.baqio.com/api/v1/product_variants" for c in fake.calls
    )
    assert fake.calls[0]["auth"] == ("u", "p")


def test_all_product_variants_empty_catalog(monkeypatch):
    fake = install_paged(monkeypatch, [])

    assert BaqioClient("u", "p").all_product_variants() == {}
    assert len(fake.calls) == 1


def test_all_product_variants_stops_at_page_cap(monkeypatch):
    cap = client_module.MAX_VARIANT_PAGES
    pages = [[{"id": n}] for n in range(1, cap + 10)]
    fake = install_paged(monkeypatch, pages)

    result = BaqioClient("u", "p").all_product_variants()

    assert len(fake.calls) == cap
    assert fake.calls[-1]["params"] == [("page", str(cap))]
    assert sorted(result) == list(range(1, cap + 1))


@pytest.mark.parametrize(
    "status_code, exception",
    [(401, BaqioAuthError), (403, BaqioAuthError), (500, BaqioUnavailableError)],
)
def test_all_product_variants_http_errors(monkeypatch, status_code, exception):
    install_paged(monkeypatch, [[{"id": 1}]], status_code=status_code)

    with pytest.raises(exception):
        BaqioClient("u", "p").all_product_variants()


def test_all_product_variants_error_on_later_page(monkeypatch):
    class FailsOnPage2(PagedGet):
        def __call__(self, url, params=None, **kwargs):
            if dict(params)["page"] == "2":
                return FakeResponse(503, {})
            return super().__call__(url, params=params, **kwargs)

    monkeypatch.setattr(
        "src.baqio.client.requests.get", FailsOnPage2([[{"id": 1}], [{"id": 2}]])
    )

    with pytest.raises(BaqioUnavailableError):
        BaqioClient("u", "p").all_product_variants()


def test_all_product_variants_network_error(monkeypatch):
    install_fake(monkeypatch, error=requests.ConnectionError())

    with pytest.raises(BaqioUnavailableError):
        BaqioClient("u", "p").all_product_variants()


def test_all_product_variants_invalid_json(monkeypatch):
    monkeypatch.setattr("src.baqio.client.requests.get", FakeGet(BadJsonResponse(200)))

    with pytest.raises(BaqioUnavailableError):
        BaqioClient("u", "p").all_product_variants()
