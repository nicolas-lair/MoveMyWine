import threading

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src import streamlit_utils
from src.app_generics.fetched_indicator import FetchedIndicator
from src.app_generics.postal_code import PostalCodeAPI
from src.baqio import app as baqio_app
from src.baqio.client import BaqioAuthError, BaqioUnavailableError
from src.baqio.destination import MSG_ZIP_NOT_FOUND
from src.baqio.order import order_label
from src.cost_calculator import CostType
from src.my_transporters.chronopost import app_calculator as chronopost_app
from src.my_transporters.chronopost.app_calculator import (
    ChronopostApp as _ChronopostAppClass,
)
from src.my_transporters.geodis import app_calculator as geodis_app
from src.my_transporters.geodis.app_calculator import GeodisApp as _GeodisAppClass
from src.my_transporters.stef import app_calculator as stef_app
from src.my_transporters.stef.app_calculator import StefApp as _StefAppClass
from src.streamlit_utils import TARIF_UNAVAILABLE_MSG, TRANSPORTER_LIST
from test.baqio.factories import make_line, make_order, make_variant


def mock_stef_indicator(url):
    default_val = [
        x
        for x in stef_app.TransporterParams.modulators.values()
        if x.modulation_link == url
    ]
    return FetchedIndicator(
        retrieved=True, valid_date=True, value=default_val[0].default
    )


def mock_chronopost_indicator(url):
    default_val = [
        x
        for x in chronopost_app.TransporterParams.modulators.values()
        if x.modulation_link == url
    ]
    return FetchedIndicator(
        retrieved=True, valid_date=True, value=default_val[0].default
    )


def mock_geodis_indicator(url):
    default_val = [
        x
        for x in geodis_app.GeodisParams.modulators.values()
        if x.modulation_link == url
    ]
    return FetchedIndicator(
        retrieved=True, valid_date=True, value=default_val[0].default
    )


def mock_postal_code_retriever():
    return pd.DataFrame.from_dict(
        {
            "full_name": [
                "75017 - Paris 17",
                "69001 - Lyon 01",
                "49100 - Angers",
                "33000 - Bordeaux",
            ],
            PostalCodeAPI.Cols.postal_code: ["75017", "69001", "49100", "33000"],
            PostalCodeAPI.Cols.commune: ["Paris 17", "Lyon 01", "Angers", "Bordeaux"],
            PostalCodeAPI.Cols.lieudit: [float("nan")] * 4,
        },
    ).set_index("full_name")


TEST_PASSWORD = "test-password"


def _new_app(authenticated: bool = True) -> AppTest:
    """Create the app with the shared password set in secrets, logged in by default."""
    app = AppTest.from_file("../src/streamlit_app.py")
    app.secrets["password"] = TEST_PASSWORD
    if authenticated:
        app.session_state["password_correct"] = True
    return app


def test_app(monkeypatch):
    monkeypatch.setattr(chronopost_app, "scrap_indicator", mock_chronopost_indicator)
    monkeypatch.setattr(stef_app, "scrap_indicator", mock_stef_indicator)
    monkeypatch.setattr(geodis_app, "scrap_indicator", mock_geodis_indicator)
    monkeypatch.setattr(
        streamlit_utils, "retrieve_postal_code", mock_postal_code_retriever
    )
    app = _new_app().run()

    assert not app.exception
    assert app.selectbox(key="transporter").value.params.name == "Stef"
    assert app.selectbox(key="destination").value == "75017 - Paris 17"
    app.number_input(key="stef_gnr_modulator").set_value(1.2).run()

    assert app.session_state.cost == 0

    ###################################################
    ##### STEF
    ###################################################

    app.number_input(key="bottle").set_value(24).run()
    assert app.session_state.detail_cost == {
        CostType.ByBottle: 47.72,  # Paris Tarif 1
        CostType.Palet: 1.0,
        CostType.Security: 0.7,
        CostType.Expedition: 5.41,
        CostType.GNRMod: 0.0,
        CostType.ColdMod: 0.0,
    }

    app.number_input(key="stef_gnr_modulator").set_value(1.42).run()
    assert app.session_state.detail_cost == {
        CostType.ByBottle: 47.72,  # Paris Tarif 1
        CostType.Palet: 1.0,
        CostType.Security: 0.7,
        CostType.Expedition: 5.41,
        CostType.GNRMod: round(0.04 * (47.72 + 5.41), 2),
        CostType.ColdMod: 0.0,
    }

    app.number_input(key="stef_froid_modulator").set_value(330).run()
    assert app.session_state.detail_cost == {
        CostType.ByBottle: 47.72,  # Paris Tarif 1
        CostType.Palet: 1.0,
        CostType.Security: 0.7,
        CostType.Expedition: 5.41,
        CostType.GNRMod: round(0.04 * (47.72 + 5.41), 2),
        CostType.ColdMod: round(0.005 * (47.72 + 5.41), 2),
    }

    ###################################################
    ##### GEODIS
    ###################################################

    app.selectbox(key="transporter").set_value(TRANSPORTER_LIST[1]).run()
    assert app.session_state.transporter.params.name == "Geodis Messagerie"
    assert app.session_state.detail_cost == {
        CostType.ByBottle: 35.5,  # Zone 4 24 bouteilles
        CostType.Security: 2.15,
        CostType.GNRMod: 0.0,
        CostType.ByDestination: 3.3,
        CostType.Palet: 5.0,
    }

    app.number_input(key="geodis_gnr_modulator").set_value(10).run()
    assert app.session_state.detail_cost == {
        CostType.ByBottle: 35.5,  # Zone 4 24 bouteilles
        CostType.Security: 2.15,
        CostType.GNRMod: 4.1,
        CostType.ByDestination: 3.3,
        CostType.Palet: 5.0,
    }

    n_bottle = 97
    app.number_input(key="bottle").set_value(n_bottle).run()
    app.selectbox(key="destination").set_value("69001 - Lyon 01").run()
    assert app.session_state.detail_cost == {
        CostType.ByBottle: round(0.71 * n_bottle, 2),  # Zone 4 97 bouteilles
        CostType.Security: 2.15,
        CostType.GNRMod: round(0.1 * (0.71 * n_bottle + 2.15 + 10.15), 2),
        CostType.ByDestination: 10.15,
        CostType.Palet: 5.0,
    }

    ###################################################
    ##### GEODIS PALETTE
    ###################################################
    app.selectbox(key="transporter").set_value(TRANSPORTER_LIST[2]).run()
    assert app.session_state.transporter.params.name == "Geodis Palette"
    # GNR modulator is shared with Geodis Messagerie, already set to 10
    assert app.number_input(key="geodis_gnr_modulator").value == 10
    assert app.session_state.detail_cost == {
        CostType.ByBottle: 136.36,
        CostType.Security: 2.15,
        CostType.GNRMod: round(0.1 * (136.36 + 2.15 + 10.15), 2),
        CostType.ByDestination: 10.15,
        CostType.Palet: 10.0,
    }

    app.number_input(key="bottle").set_value(600).run()  # 738 kg -> 2 palettes
    assert app.session_state.detail_cost[CostType.ByBottle] == 219.12
    assert app.session_state.detail_cost[CostType.Palet] == 20.0

    app.number_input(key="bottle").set_value(1200).run()  # 3 palettes, hors grille
    assert not app.exception
    assert app.session_state.detail_cost == {}
    assert app.session_state.cost == 0
    assert any(w.value == TARIF_UNAVAILABLE_MSG for w in app.warning)

    ###################################################
    ##### CHRONOPOST
    ###################################################
    app.selectbox(key="destination").set_value("75017 - Paris 17").run()
    app.number_input(key="bottle").set_value(24).run()
    app.selectbox(key="transporter").set_value(TRANSPORTER_LIST[3]).run()
    assert app.session_state.transporter.params.name == "Chronopost"
    assert app.session_state.detail_cost == {
        CostType.ByBottle: round(21.06 + 14.52 * 1.13, 2),
        CostType.ByPackage: 1.5,
        CostType.Expedition: 0.89,
        CostType.GNRMod: 0,
    }

    app.number_input(key="chronopost_gnr_modulator").set_value(15).run()
    assert app.session_state.detail_cost == {
        CostType.ByBottle: round(21.06 + 14.52 * 1.13, 2),
        CostType.ByPackage: 1.5,
        CostType.Expedition: 0.89,
        CostType.GNRMod: 5.98,
    }

    app.number_input(key="bottle").set_value(6).run()
    assert app.session_state.detail_cost == {
        CostType.ByBottle: 21.06,
        CostType.ByPackage: 0.0,
        CostType.Expedition: 0.89,
        CostType.GNRMod: 3.29,
    }

    app.number_input(key="chronopost_gnr_modulator").set_value(0).run()
    app.number_input(key="bottle").set_value(12).run()
    assert app.session_state.detail_cost == {
        CostType.ByBottle: 21.06,
        CostType.ByPackage: 0.0,
        CostType.Expedition: 0.89,
        CostType.GNRMod: 0,
    }

    app.number_input(key="bottle").set_value(18).run()
    assert app.session_state.detail_cost == {
        CostType.ByBottle: round(21.06 + 7.14 * 1.13, 2),
        CostType.ByPackage: 0.0,
        CostType.Expedition: 0.89,
        CostType.GNRMod: 0,
    }

    ###################################################
    ##### Back to STEF
    ###################################################

    app.selectbox(key="transporter").set_value(TRANSPORTER_LIST[0]).run()
    assert app.session_state.transporter.params.name == "Stef"

    app.selectbox(key="destination").set_value("75017 - Paris 17").run()
    app.number_input(key="stef_gnr_modulator").set_value(1.2).run()
    app.number_input(key="stef_froid_modulator").set_value(300.0).run()
    app.number_input(key="bottle").set_value(36).run()
    assert app.session_state.detail_cost == {
        CostType.ByBottle: 47.72,  # Paris Tarif 1
        CostType.Palet: 1.0,
        CostType.Security: 0.7,
        CostType.Expedition: 5.41,
        CostType.GNRMod: 0,
        CostType.ColdMod: 0.0,
    }

    app.number_input(key="bottle").set_value(48).run()
    assert app.session_state.detail_cost == {
        CostType.ByBottle: 61.89,  # Paris Tarif 2
        CostType.Palet: 1.0,
        CostType.Security: 0.7,
        CostType.Expedition: 5.41,
        CostType.GNRMod: 0,
        CostType.ColdMod: 0.0,
    }

    app.selectbox(key="destination").set_value("69001 - Lyon 01").run()
    assert app.session_state.detail_cost == {
        CostType.ByBottle: 64.29,  # Lyon Tarif 2
        CostType.Palet: 1.0,
        CostType.Security: 0.7,
        CostType.Expedition: 5.41,
        CostType.GNRMod: 0,
        CostType.ColdMod: 0.0,
    }

    app.number_input(key="bottle").set_value(130).run()
    assert app.session_state.detail_cost == {
        # 0.88 = Price per bottle for 130 bottles to Lyon (69)
        CostType.ByBottle: round(0.88 * 130, 2),
        CostType.Palet: 1.0,
        CostType.Security: 0.7,
        CostType.Expedition: 5.41,
        CostType.GNRMod: 0,
        CostType.ColdMod: 0.0,
    }

    app.number_input(key="bottle").set_value(170).run()
    app.selectbox(key="destination").set_value("49100 - Angers").run()
    assert app.session_state.detail_cost == {
        # 0.44 = Price per bottle for 170 bottles to Angers (49)
        CostType.ByBottle: round(170 * 0.44, 2),
        CostType.Palet: 1.0,
        CostType.Security: 0.7,
        CostType.Expedition: 5.41,
        CostType.GNRMod: 0.0,
        CostType.ColdMod: 0.0,
    }


# ---------------------------------------------------------------------------
# Helpers for comparison tab tests
# ---------------------------------------------------------------------------
# Class-level mocks (receive modconfig, bypass @st.cache_data)


def _ok_indicator(modconfig):
    return FetchedIndicator(retrieved=True, valid_date=True, value=modconfig.default)


def _failing_indicator(modconfig):
    return FetchedIndicator(retrieved=False)


def _invalid_date_indicator(modconfig):
    return FetchedIndicator(retrieved=True, valid_date=False, value=14.89)


def _build_app(monkeypatch, stef_mock=None, geodis_mock=None, chronopost_mock=None):
    """Build a test app patching scrap_indicator at class level to bypass @st.cache_data."""
    monkeypatch.setattr(
        _StefAppClass, "scrap_indicator", staticmethod(stef_mock or _ok_indicator)
    )
    monkeypatch.setattr(
        _GeodisAppClass, "scrap_indicator", staticmethod(geodis_mock or _ok_indicator)
    )
    monkeypatch.setattr(
        _ChronopostAppClass,
        "scrap_indicator",
        staticmethod(chronopost_mock or _ok_indicator),
    )
    monkeypatch.setattr(
        streamlit_utils, "retrieve_postal_code", mock_postal_code_retriever
    )
    return _new_app().run()


def _indicator_expander(app):
    return next(e for e in app.expander if "Indicateurs" in e.label)


# ---------------------------------------------------------------------------
# Comparison tab — indicator alert logic
# ---------------------------------------------------------------------------


class TestComparisonIndicators:
    def test_no_bottles_shows_info(self, monkeypatch):
        """Info message displayed when no bottles entered."""
        app = _build_app(monkeypatch)
        assert not app.exception
        assert any("bouteilles" in info.value.lower() for info in app.info)

    def test_all_indicators_ok(self, monkeypatch):
        """✅ expander shown when all indicators retrieved with a valid date."""
        app = _build_app(monkeypatch)
        app.number_input(key="bottle").set_value(24).run()
        assert not app.exception
        expander = _indicator_expander(app)
        assert "✅" in expander.label
        assert "⚠️" not in expander.label

    def test_indicator_not_retrieved(self, monkeypatch):
        """⚠️ 1 alerte when one indicator fails to be retrieved."""
        app = _build_app(monkeypatch, chronopost_mock=_failing_indicator)
        app.number_input(key="bottle").set_value(24).run()
        assert not app.exception
        expander = _indicator_expander(app)
        assert "⚠️" in expander.label
        assert "1 alerte" in expander.label

    def test_geodis_indicator_not_retrieved(self, monkeypatch):
        """The Geodis indicator is shared by both offers → a single alert naming both."""
        app = _build_app(monkeypatch, geodis_mock=_failing_indicator)
        app.number_input(key="bottle").set_value(24).run()
        assert not app.exception
        expander = _indicator_expander(app)
        assert "⚠️" in expander.label
        assert "1 alerte" in expander.label
        assert any(
            "Geodis Messagerie, Geodis Palette / GNR" in w.value for w in app.warning
        )

    def test_indicator_invalid_date(self, monkeypatch):
        """⚠️ 1 alerte when one indicator has an invalid date."""
        app = _build_app(monkeypatch, chronopost_mock=_invalid_date_indicator)
        app.number_input(key="bottle").set_value(24).run()
        assert not app.exception
        expander = _indicator_expander(app)
        assert "⚠️" in expander.label
        assert "1 alerte" in expander.label

    def test_multiple_alerts(self, monkeypatch):
        """Alert count reflects all failing modulators (Stef has 2, Geodis offers share 1 → 3 total)."""
        app = _build_app(
            monkeypatch,
            stef_mock=_failing_indicator,
            geodis_mock=_failing_indicator,
        )
        app.number_input(key="bottle").set_value(24).run()
        assert not app.exception
        expander = _indicator_expander(app)
        assert "⚠️" in expander.label
        assert "3 alertes" in expander.label


# ---------------------------------------------------------------------------
# Comparison tab — cost computation
# ---------------------------------------------------------------------------


class TestComparisonCosts:
    def test_all_transporters_present_with_positive_costs(self, monkeypatch):
        """Totals dataframe contains all active transporters with positive costs."""
        app = _build_app(monkeypatch)
        app.number_input(key="bottle").set_value(24).run()
        assert not app.exception

        transporter_names = {t.params.name for t in TRANSPORTER_LIST}
        for element in app.dataframe:
            df = element.value
            if hasattr(df, "data"):  # unwrap Styler if needed
                df = df.data
            if set(df.index) == transporter_names:
                assert all(df.iloc[:, 0] > 0), (
                    "All transporter costs should be positive"
                )
                return
        pytest.fail("Totals dataframe not found among page elements")

    def test_costs_independent_of_selected_transporter(self, monkeypatch):
        """Comparison costs are computed for all transporters regardless of which is selected in tab1."""
        app = _build_app(monkeypatch)
        app.number_input(key="bottle").set_value(24).run()
        app.selectbox(key="transporter").set_value(TRANSPORTER_LIST[1]).run()
        assert not app.exception
        assert app.session_state.transporter.params.name == "Geodis Messagerie"

        transporter_names = {t.params.name for t in TRANSPORTER_LIST}
        found = False
        for element in app.dataframe:
            df = element.value
            if hasattr(df, "data"):
                df = df.data
            if set(df.index) == transporter_names:
                found = True
                assert all(df.iloc[:, 0] > 0)
        assert found, "Totals dataframe not found"


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


class TestAuthentication:
    def test_app_hidden_before_login(self, monkeypatch):
        """Only the password field is shown until the user logs in."""
        monkeypatch.setattr(
            streamlit_utils, "retrieve_postal_code", mock_postal_code_retriever
        )
        app = _new_app(authenticated=False).run()
        assert not app.exception
        assert len(app.text_input) == 1
        assert len(app.selectbox) == 0

    def test_wrong_password(self, monkeypatch):
        monkeypatch.setattr(
            streamlit_utils, "retrieve_postal_code", mock_postal_code_retriever
        )
        app = _new_app(authenticated=False).run()
        app.text_input(key="password").input("wrong").run()
        assert not app.exception
        assert app.session_state.password_correct is False
        assert any("incorrect" in e.value for e in app.error)
        assert len(app.selectbox) == 0

    def test_right_password(self, monkeypatch):
        monkeypatch.setattr(
            _StefAppClass, "scrap_indicator", staticmethod(_ok_indicator)
        )
        monkeypatch.setattr(
            _GeodisAppClass, "scrap_indicator", staticmethod(_ok_indicator)
        )
        monkeypatch.setattr(
            _ChronopostAppClass, "scrap_indicator", staticmethod(_ok_indicator)
        )
        monkeypatch.setattr(
            streamlit_utils, "retrieve_postal_code", mock_postal_code_retriever
        )
        app = _new_app(authenticated=False).run()
        app.text_input(key="password").input(TEST_PASSWORD).run()
        assert not app.exception
        assert app.session_state.password_correct is True
        assert "password" not in app.session_state
        assert app.selectbox(key="transporter").value.params.name == "Stef"


# ---------------------------------------------------------------------------
# Baqio import widget
# ---------------------------------------------------------------------------

BOTTLE_VARIANT, MAGNUM_VARIANT, BULK_VARIANT = 2, 3, 4
BAQIO_VARIANTS = {
    BOTTLE_VARIANT: make_variant(BOTTLE_VARIANT, 750),
    MAGNUM_VARIANT: make_variant(MAGNUM_VARIANT, 1500),
    BULK_VARIANT: make_variant(BULK_VARIANT, 0, kind="bulk"),
}


class FakeBaqioClient:
    """Stand-in for BaqioClient: one list per recent_orders call (last one repeats)."""

    def __init__(
        self,
        lists=(),
        variants=None,
        raises=None,
        raises_on="recent",
        search_results=(),
        search_raises=None,
        catalog=None,
        catalog_raises=None,
        catalog_gate=None,
    ):
        # catalog: dict returned by all_product_variants(). Default {} (empty
        # catalogue) so that existing tests keep falling back on the per-id
        # get_product_variant calls they assert on.
        self.catalog = {} if catalog is None else catalog
        self.catalog_raises = catalog_raises
        self.catalog_gate = catalog_gate  # threading.Event the call blocks on
        self.catalog_calls = 0
        self.catalog_started = threading.Event()  # set on every call (thread-safe)
        self.search_results = list(search_results)
        self.search_raises = search_raises
        self.search_texts = []
        self.lists = list(lists)
        self.variants = BAQIO_VARIANTS if variants is None else variants
        self.raises = raises
        self.raises_on = raises_on
        self.recent_calls = 0
        self.variant_calls = []

    def recent_orders(self):
        self.recent_calls += 1
        if self.raises and self.raises_on == "recent":
            raise self.raises
        if not self.lists:
            return []
        index = min(self.recent_calls, len(self.lists)) - 1
        return self.lists[index]

    def search_orders(self, text):
        self.search_texts.append(text)
        if self.search_raises:
            raise self.search_raises
        return self.search_results

    def all_product_variants(self):
        self.catalog_calls += 1
        self.catalog_started.set()
        if self.catalog_gate is not None:
            self.catalog_gate.wait(timeout=10)
        if self.catalog_raises:
            raise self.catalog_raises
        return self.catalog

    def get_product_variant(self, variant_id):
        self.variant_calls.append(variant_id)
        if self.raises and self.raises_on == "variants":
            raise self.raises
        return self.variants.get(variant_id)


def _order(id, customer, bottles=0, magnums=0, extra_lines=(), **kwargs):
    lines = []
    if bottles:
        lines.append(make_line(BOTTLE_VARIANT, bottles))
    if magnums:
        lines.append(make_line(MAGNUM_VARIANT, magnums, description="Magnum (1,5 l)"))
    lines.extend(extra_lines)
    return make_order(
        id=id,
        name=f"#{id}",
        customer=customer,
        lines=lines,
        bottle_quantity=str(float(bottles + magnums)),
        **kwargs,
    )


def _baqio_app(monkeypatch, fake, with_secrets=True, patch_client=True, secrets=None):
    """Return the app after its first run (Baqio orders are preloaded by then)."""
    monkeypatch.setattr(_StefAppClass, "scrap_indicator", staticmethod(_ok_indicator))
    monkeypatch.setattr(_GeodisAppClass, "scrap_indicator", staticmethod(_ok_indicator))
    monkeypatch.setattr(
        _ChronopostAppClass, "scrap_indicator", staticmethod(_ok_indicator)
    )
    monkeypatch.setattr(
        streamlit_utils, "retrieve_postal_code", mock_postal_code_retriever
    )
    if patch_client:
        monkeypatch.setattr(baqio_app, "get_client", lambda: fake)
    app = _new_app()
    if with_secrets:
        app.secrets["baqio"] = secrets or {"user": "u", "password": "p"}
    return app.run()


def _refresh(app):
    app.button(key="baqio_refresh").click().run()
    return app


def _select(app, ids):
    app.multiselect(key="baqio_selected").set_value(ids).run()
    return app


def _type(app, text):
    """Simulate typing free text in the multiselect (accept_new_options).

    AppTest has no API for new options: Multiselect.set_value only stores a list
    that is sent as the widget's string array, which is what the frontend sends for
    a typed value (the raw text next to the labels of the selected options). The
    implementation's format_func must therefore accept a str (return it as is).
    """
    widget = app.multiselect(key="baqio_selected")
    widget.set_value([*widget.value, text]).run()
    return app


def _selected(app):
    return list(app.session_state.baqio_selected)


def _texts(elements):
    return [e.value for e in elements]


def _has_main_radio(app):
    return any(r.key == "baqio_main" for r in app.radio)


class TestBaqioImport:
    def test_hidden_without_secrets(self, monkeypatch):
        app = _baqio_app(monkeypatch, FakeBaqioClient(), with_secrets=False)
        assert not app.exception
        assert all(e.label != baqio_app.EXPANDER_LABEL for e in app.expander)

    def test_shown_with_secrets(self, monkeypatch):
        app = _baqio_app(monkeypatch, FakeBaqioClient())
        assert not app.exception
        assert any(e.label == baqio_app.EXPANDER_LABEL for e in app.expander)

    def test_no_search_widgets(self, monkeypatch):
        app = _baqio_app(monkeypatch, FakeBaqioClient([[_order(1, "Client A", 6)]]))
        assert not app.exception
        assert all(t.key != "baqio_query" for t in app.text_input)
        assert all(b.key != "baqio_search" for b in app.button)
        assert not hasattr(baqio_app, "MSG_EMPTY_QUERY")
        assert any(b.key == "baqio_refresh" for b in app.button)

    def test_preload_on_first_run(self, monkeypatch):
        fake = FakeBaqioClient([[_order(1, "Client A", bottles=6)]])
        app = _baqio_app(monkeypatch, fake)
        assert not app.exception
        assert fake.recent_calls == 1
        options = app.multiselect(key="baqio_selected").options
        assert len(options) == 1
        assert options[0].startswith("#1 ")

    def test_single_preload_across_reruns(self, monkeypatch):
        order = _order(1, "Client A", bottles=6)
        fake = FakeBaqioClient([[order]])
        app = _baqio_app(monkeypatch, fake)
        _select(app, [1])
        app.number_input(key="bottle").set_value(7).run()
        app.run()
        assert not app.exception
        assert fake.recent_calls == 1

    def test_refresh_calls_again(self, monkeypatch):
        order_a = _order(1, "Client A", bottles=12)
        order_c = _order(
            3, "Client C", bottles=6, created_at="2026-09-22T10:00:00+02:00"
        )
        fake = FakeBaqioClient([[order_a], [order_a, order_c]])
        app = _baqio_app(monkeypatch, fake)
        assert len(app.multiselect(key="baqio_selected").options) == 1
        _refresh(app)
        assert not app.exception
        assert fake.recent_calls == 2
        options = app.multiselect(key="baqio_selected").options
        assert order_label(order_c) in options
        assert order_label(order_a) in options
        app.run()
        assert fake.recent_calls == 2

    def test_no_result(self, monkeypatch):
        fake = FakeBaqioClient([[]])
        app = _baqio_app(monkeypatch, fake)
        assert not app.exception
        assert fake.recent_calls == 1
        assert baqio_app.MSG_NO_RESULT in _texts(app.info) + _texts(app.warning)

    def test_load_single_order(self, monkeypatch):
        order = _order(1, "Client A", bottles=24, magnums=3)
        app = _baqio_app(monkeypatch, FakeBaqioClient([[order]]))
        _select(app, [1])
        assert not _has_main_radio(app)
        assert not app.exception
        assert app.session_state.bottle == 24
        assert app.session_state.magnum == 3
        assert app.session_state.destination == "33000 - Bordeaux"
        assert not _has_main_radio(app)
        assert app.session_state.cost > 0
        group = app.session_state.baqio_group
        assert (group.bottles, group.magnums) == (24, 3)
        assert [o.id for o in group.orders] == [1]

    def test_load_group_main_recipient(self, monkeypatch):
        first = _order(1, "Client A", bottles=12)
        second = _order(2, "Client B", magnums=6, zip="69001", city="LYON 01")
        app = _baqio_app(monkeypatch, FakeBaqioClient([[first, second]]))
        _select(app, [1, 2])
        assert _has_main_radio(app)
        app.radio(key="baqio_main").set_value(2).run()
        assert not app.exception
        assert app.session_state.bottle == 12
        assert app.session_state.magnum == 6
        assert app.session_state.destination == "69001 - Lyon 01"
        mixed = baqio_app.MSG_MIXED_ADDRESSES.format(customer="Client B")
        assert mixed in _texts(app.info)
        group = app.session_state.baqio_group
        assert [o.id for o in group.orders] == [2, 1]  # main recipient first

    def test_city_name_mismatch_no_warning(self, monkeypatch):
        # Baqio says "Paris", the destination entry is "Paris 17": zip decides
        order = _order(1, "Client A", bottles=12, zip="75017", city="Paris")
        app = _baqio_app(monkeypatch, FakeBaqioClient([[order]]))
        app.selectbox(key="destination").set_value("33000 - Bordeaux").run()
        _select(app, [1])
        assert not app.exception
        assert app.session_state.destination == "75017 - Paris 17"
        assert _texts(app.warning) == []

    def test_group_with_customerless_order(self, monkeypatch):
        first = _order(1, "Client A", bottles=12)
        second = _order(2, "x", magnums=6)
        second["customer"] = None
        app = _baqio_app(monkeypatch, FakeBaqioClient([[first, second]]))
        _select(app, [1, 2])
        assert not app.exception
        assert _has_main_radio(app)
        assert len(app.radio(key="baqio_main").options) == 2
        assert not app.exception
        assert app.session_state.bottle == 12
        assert app.session_state.magnum == 6

    def test_malformed_orders_never_break_the_form(self, monkeypatch):
        valid = _order(1, "Client A", bottles=12)
        bad_date = _order(2, "Client B", bottles=6)
        bad_date["created_at"] = None
        bad_string = _order(5, "Client E", bottles=6)
        bad_string["created_at"] = "pas une date"
        no_qty = _order(3, "Client C", bottles=6)
        no_qty["bottle_quantity"] = None
        fake = FakeBaqioClient([[valid, bad_date, bad_string, no_qty]])
        app = _baqio_app(monkeypatch, fake)
        assert not app.exception
        options = app.multiselect(key="baqio_selected").options
        assert len(options) == 2
        assert any(o.startswith("#1 ") for o in options)
        assert any(o.startswith("#3 ") and o.endswith("0 btl") for o in options)
        warnings = _texts(app.warning)
        assert baqio_app.MSG_INVALID_ORDER.format(order="#2") in warnings
        assert baqio_app.MSG_INVALID_ORDER.format(order="#5") in warnings
        app.number_input(key="bottle").set_value(7).run()
        assert not app.exception
        assert app.session_state.bottle == 7

    def test_order_without_lines_refused_on_load(self, monkeypatch):
        broken = _order(4, "Client D", bottles=6)
        del broken["order_lines_not_deleted"]
        app = _baqio_app(monkeypatch, FakeBaqioClient([[broken]]))
        app.number_input(key="bottle").set_value(5).run()
        _select(app, [4])
        assert not app.exception
        assert baqio_app.MSG_INVALID_ORDER.format(order="#4") in _texts(app.warning)
        assert app.session_state.bottle == 5
        assert app.session_state.magnum == 0

    def test_options_sorted_and_filtered(self, monkeypatch):
        old = _order(1, "Client A", bottles=6, created_at="2026-09-20T10:00:00+02:00")
        recent = _order(
            2, "Client B", bottles=6, created_at="2026-09-23T10:00:00+02:00"
        )
        middle = _order(
            3, "Client C", bottles=6, created_at="2026-09-21T10:00:00+02:00"
        )
        invoiced = _order(4, "Client D", bottles=6)
        invoiced["state"] = "invoiced"
        validated = _order(
            5, "Client E", bottles=6, created_at="2026-09-19T10:00:00+02:00"
        )
        validated["state"] = "validated"
        fake = FakeBaqioClient([[old, recent, middle, invoiced, validated]])
        app = _baqio_app(monkeypatch, fake)
        assert not app.exception
        options = app.multiselect(key="baqio_selected").options
        assert [o.split(" ")[0] for o in options] == ["#2", "#3", "#1", "#5"]

    def test_negative_quantity_refused(self, monkeypatch):
        order = _order(
            1,
            "Client A",
            bottles=12,
            extra_lines=[make_line(BOTTLE_VARIANT, "-6")],
        )
        app = _baqio_app(monkeypatch, FakeBaqioClient([[order]]))
        app.number_input(key="bottle").set_value(5).run()
        _select(app, [1])
        assert not app.exception
        assert baqio_app.MSG_OUT_OF_RANGE in _texts(app.warning) + _texts(app.error)
        assert app.session_state.bottle == 5

    def test_misconfigured_secrets(self, monkeypatch):
        app = _baqio_app(
            monkeypatch,
            FakeBaqioClient(),
            patch_client=False,
            secrets={"user": "u"},
        )
        assert not app.exception
        assert baqio_app.MSG_AUTH in _texts(app.error)
        app.number_input(key="bottle").set_value(24).run()
        assert not app.exception
        assert app.session_state.cost > 0

    def test_mixed_addresses_with_customerless_main(self, monkeypatch):
        first = _order(1, "Client A", bottles=12)
        second = _order(2, "x", magnums=6, zip="69001", city="LYON 01")
        second["customer"] = None
        app = _baqio_app(monkeypatch, FakeBaqioClient([[first, second]]))
        _select(app, [1, 2])
        app.radio(key="baqio_main").set_value(2).run()
        assert not app.exception
        assert baqio_app.MSG_MIXED_ADDRESSES.format(customer="#2") in _texts(app.info)

    def test_selection_kept_across_refresh(self, monkeypatch):
        order_a = _order(1, "Client A", bottles=12)
        order_c = _order(
            3, "Client C", bottles=6, created_at="2026-09-22T10:00:00+02:00"
        )
        # the refresh no longer returns order A
        app = _baqio_app(monkeypatch, FakeBaqioClient([[order_a], [order_c]]))
        _select(app, [1])
        assert app.session_state.bottle == 12
        _refresh(app)
        assert not app.exception
        assert app.session_state.baqio_selected == [1]
        options = app.multiselect(key="baqio_selected").options
        assert order_label(order_a) in options
        assert order_label(order_c) in options
        # most recent first
        assert options.index(order_label(order_c)) < options.index(order_label(order_a))
        # the kept selection is still loadable together with a new order
        _select(app, [1, 3])
        assert not app.exception
        assert app.session_state.bottle == 18

    def test_ignored_lines_warning(self, monkeypatch):
        order = _order(
            1,
            "Client A",
            bottles=12,
            extra_lines=[make_line(BULK_VARIANT, 100, description="Vrac")],
        )
        app = _baqio_app(monkeypatch, FakeBaqioClient([[order]]))
        _select(app, [1])
        assert not app.exception
        assert app.session_state.bottle == 12
        assert any(w.value.startswith("Lignes ignorées (#") for w in app.warning)

    def test_no_bottle_refused(self, monkeypatch):
        order = _order(
            1,
            "Client A",
            extra_lines=[make_line(BULK_VARIANT, 100, description="Vrac")],
        )
        app = _baqio_app(monkeypatch, FakeBaqioClient([[order]]))
        app.number_input(key="bottle").set_value(5).run()
        _select(app, [1])
        assert not app.exception
        assert baqio_app.MSG_NO_BOTTLE in _texts(app.warning) + _texts(app.error)
        assert app.session_state.bottle == 5
        assert app.session_state.magnum == 0

    def test_out_of_range_refused(self, monkeypatch):
        order = _order(1, "Client A", bottles=1206)
        app = _baqio_app(monkeypatch, FakeBaqioClient([[order]]))
        app.number_input(key="bottle").set_value(5).run()
        _select(app, [1])
        assert not app.exception
        assert baqio_app.MSG_OUT_OF_RANGE in _texts(app.warning) + _texts(app.error)
        assert app.session_state.bottle == 5

    def test_unknown_zip_keeps_destination(self, monkeypatch):
        order = _order(1, "Client A", bottles=12, zip="99999", city="NOWHERE")
        app = _baqio_app(monkeypatch, FakeBaqioClient([[order]]))
        assert app.session_state.destination == "75017 - Paris 17"
        _select(app, [1])
        assert not app.exception
        assert app.session_state.bottle == 12
        assert app.session_state.destination == "75017 - Paris 17"
        assert MSG_ZIP_NOT_FOUND.format(zip="99999") in _texts(app.warning)

    @pytest.mark.parametrize(
        "error, level, message",
        [
            (BaqioAuthError("401"), "error", baqio_app.MSG_AUTH),
            (BaqioUnavailableError("down"), "warning", baqio_app.MSG_UNAVAILABLE),
        ],
    )
    @pytest.mark.parametrize("raises_on", ["recent", "variants"])
    def test_client_errors(self, monkeypatch, error, level, message, raises_on):
        order = _order(1, "Client A", bottles=12)
        fake = FakeBaqioClient([[order]], raises=error, raises_on=raises_on)
        if raises_on == "recent":
            app = _baqio_app(monkeypatch, fake)  # preload fails on first run
        else:
            fake.raises = None
            app = _baqio_app(monkeypatch, fake)
            fake.raises = error
            _select(app, [1])
        assert not app.exception
        assert message in _texts(getattr(app, level))
        assert app.session_state.bottle == 0
        # manual entry and cost computation still work
        app.number_input(key="bottle").set_value(24).run()
        assert not app.exception
        assert app.session_state.bottle == 24
        assert app.session_state.cost > 0

    def test_refresh_recovers_after_error(self, monkeypatch):
        order = _order(1, "Client A", bottles=12)
        fake = FakeBaqioClient([[order]], raises=BaqioUnavailableError("down"))
        app = _baqio_app(monkeypatch, fake)
        assert baqio_app.MSG_UNAVAILABLE in _texts(app.warning)
        fake.raises = None
        _refresh(app)
        assert not app.exception
        assert fake.recent_calls == 2
        assert len(app.multiselect(key="baqio_selected").options) == 1

    def test_variants_cached(self, monkeypatch):
        order = _order(1, "Client A", bottles=24, magnums=3)
        fake = FakeBaqioClient([[order]])
        app = _baqio_app(monkeypatch, fake)
        _select(app, [1])
        _select(app, [])
        _select(app, [1])
        assert not app.exception
        assert app.session_state.bottle == 24
        assert sorted(fake.variant_calls) == [BOTTLE_VARIANT, MAGNUM_VARIANT]

    def test_load_button_removed_and_refresh_label(self, monkeypatch):
        app = _baqio_app(monkeypatch, FakeBaqioClient([[_order(1, "Client A", 6)]]))
        assert all(b.key != "baqio_load" for b in app.button)
        assert all(b.label != "Charger" for b in app.button)
        assert app.button(key="baqio_refresh").label == "Recharger Baqio"

    def test_selection_loads_immediately(self, monkeypatch):
        order = _order(1, "Client A", bottles=12, zip="69001", city="LYON 01")
        app = _baqio_app(monkeypatch, FakeBaqioClient([[order]]))
        _select(app, [1])
        assert not app.exception
        assert app.session_state.bottle == 12
        assert app.session_state.destination == "69001 - Lyon 01"
        assert app.session_state.baqio_group is not None

    def test_main_recipient_change_loads_new_destination(self, monkeypatch):
        first = _order(1, "Client A", bottles=12)
        second = _order(2, "Client B", magnums=6, zip="69001", city="LYON 01")
        app = _baqio_app(monkeypatch, FakeBaqioClient([[first, second]]))
        _select(app, [1, 2])
        assert app.session_state.destination == "33000 - Bordeaux"
        app.radio(key="baqio_main").set_value(2).run()
        assert not app.exception
        assert app.session_state.destination == "69001 - Lyon 01"
        group = app.session_state.baqio_group
        assert [o.id for o in group.orders] == [2, 1]

    def test_adding_second_order_updates_totals(self, monkeypatch):
        first = _order(1, "Client A", bottles=12)
        second = _order(2, "Client B", bottles=6, magnums=2)
        app = _baqio_app(monkeypatch, FakeBaqioClient([[first, second]]))
        _select(app, [1])
        assert (app.session_state.bottle, app.session_state.magnum) == (12, 0)
        _select(app, [1, 2])
        assert not app.exception
        assert (app.session_state.bottle, app.session_state.magnum) == (18, 2)
        assert len(app.session_state.baqio_group.orders) == 2

    def test_deselecting_everything_keeps_fields(self, monkeypatch):
        first = _order(1, "Client A", bottles=12)
        second = _order(2, "Client B", bottles=6, zip="69001", city="LYON 01")
        app = _baqio_app(monkeypatch, FakeBaqioClient([[first, second]]))
        _select(app, [1, 2])
        assert _split_dataframe(app) is not None
        _select(app, [])
        assert not app.exception
        assert app.session_state.bottle == 18
        assert app.session_state.destination == "33000 - Bordeaux"
        assert app.session_state.baqio_group is None
        assert _split_dataframe(app) is None

    def test_deselecting_everything_clears_messages(self, monkeypatch):
        order = _order(1, "Client A", bottles=1206)
        app = _baqio_app(monkeypatch, FakeBaqioClient([[order]]))
        _select(app, [1])
        assert baqio_app.MSG_OUT_OF_RANGE in _texts(app.warning) + _texts(app.error)
        _select(app, [])
        assert not app.exception
        assert baqio_app.MSG_OUT_OF_RANGE not in _texts(app.warning) + _texts(app.error)
        assert app.session_state.baqio_group is None

    def test_refused_load_after_valid_group_resets_group(self, monkeypatch):
        good = _order(1, "Client A", bottles=12)
        huge = _order(2, "Client B", bottles=1206)
        app = _baqio_app(monkeypatch, FakeBaqioClient([[good, huge]]))
        _select(app, [1])
        assert app.session_state.baqio_group is not None
        assert app.session_state.bottle == 12
        _select(app, [1, 2])
        assert not app.exception
        assert baqio_app.MSG_OUT_OF_RANGE in _texts(app.warning) + _texts(app.error)
        assert app.session_state.baqio_group is None
        assert app.session_state.bottle == 12
        assert _split_dataframe(app) is None

    def test_variants_error_after_valid_group_resets_group(self, monkeypatch):
        good = _order(1, "Client A", bottles=12)
        other = _order(2, "Client B", bottles=6)
        other["order_lines_not_deleted"][0]["product_variant_id"] = 99
        fake = FakeBaqioClient([[good, other]])
        app = _baqio_app(monkeypatch, fake)
        _select(app, [1])
        assert app.session_state.baqio_group is not None
        fake.raises = BaqioUnavailableError("down")
        fake.raises_on = "variants"
        _select(app, [1, 2])
        assert not app.exception
        assert baqio_app.MSG_UNAVAILABLE in _texts(app.warning)
        assert app.session_state.baqio_group is None
        assert app.session_state.bottle == 12


def _split_dataframe(app):
    for element in app.dataframe:
        df = element.value
        if hasattr(df, "data"):  # unwrap Styler if needed
            df = df.data
        if list(df.columns) == baqio_app.SPLIT_COLUMNS:
            return df
    return None


def _load_two_orders(monkeypatch):
    first = _order(1, "Client A", bottles=24)
    second = _order(2, "Client B", bottles=12)
    app = _baqio_app(monkeypatch, FakeBaqioClient([[first, second]]))
    _select(app, [1, 2])
    return app


def _leaves(block):
    """Depth-first flattening of an AppTest block into its leaf elements."""
    children = getattr(block, "children", None)
    if not children:
        return [block]
    leaves = []
    for key in sorted(children):
        leaves.extend(_leaves(children[key]))
    return leaves


def _is_split_dataframe(element):
    if type(element).__name__ != "Dataframe":
        return False
    df = element.value
    df = getattr(df, "data", df)
    return list(df.columns) == baqio_app.SPLIT_COLUMNS


def _detailed_tab_leaves(app):
    tab = next(t for t in app.tabs if t.label == "Tarif détaillé")
    return _leaves(tab)


class TestBaqioGroupSplit:
    def test_split_table_for_group(self, monkeypatch):
        app = _load_two_orders(monkeypatch)
        assert not app.exception
        assert app.session_state.cost > 0
        df = _split_dataframe(app)
        assert df is not None
        assert len(df) == 2
        assert round(df["Montant HT (€)"].sum(), 2) == round(app.session_state.cost, 2)
        assert list(df["Part (%)"]) == [66.7, 33.3]

    def test_split_rendered_before_total_amount(self, monkeypatch):
        app = _load_two_orders(monkeypatch)
        assert not app.exception
        leaves = _detailed_tab_leaves(app)
        split_index = next(i for i, e in enumerate(leaves) if _is_split_dataframe(e))
        total_index = next(
            i
            for i, e in enumerate(leaves)
            if type(e).__name__ == "Markdown" and "€ HT" in e.value
        )
        assert split_index < total_index
        # and after the surcharges block
        surcharge_indexes = [
            i for i, e in enumerate(leaves) if type(e).__name__ == "NumberInput"
        ]
        assert surcharge_indexes
        assert max(surcharge_indexes) < split_index

    def test_no_split_for_single_order(self, monkeypatch):
        order = _order(1, "Client A", bottles=24)
        app = _baqio_app(monkeypatch, FakeBaqioClient([[order]]))
        _select(app, [1])
        assert not app.exception
        assert app.session_state.cost > 0
        assert _split_dataframe(app) is None

    def test_split_disabled_after_manual_edit(self, monkeypatch):
        app = _load_two_orders(monkeypatch)
        app.number_input(key="bottle").set_value(30).run()
        assert not app.exception
        assert baqio_app.MSG_MANUAL_EDIT in _texts(app.info)
        assert _split_dataframe(app) is None

    def test_split_follows_transporter_change(self, monkeypatch):
        app = _load_two_orders(monkeypatch)
        before = app.session_state.cost
        app.selectbox(key="transporter").set_value(TRANSPORTER_LIST[1]).run()
        assert not app.exception
        assert app.session_state.cost > 0
        assert app.session_state.cost != before
        df = _split_dataframe(app)
        assert df is not None
        assert round(df["Montant HT (€)"].sum(), 2) == round(app.session_state.cost, 2)


class TestBaqioTypedOrder:
    """Order outside the preloaded list: typed text triggers search_orders."""

    def _app(self, monkeypatch, found=(), **kwargs):
        preloaded = [_order(1, "Client A", bottles=6)]
        fake = FakeBaqioClient([preloaded], search_results=list(found), **kwargs)
        return _baqio_app(monkeypatch, fake), fake

    def test_constants(self):
        assert baqio_app.MSG_SEARCH_NO_RESULT == (
            "Aucune commande non facturée pour « {text} »."
        )
        assert baqio_app.MSG_SEARCH_CHOOSE == (
            "{count} commandes trouvées pour « {text} » "
            "— ajoutées à la liste, sélectionnez-les."
        )

    def test_single_result_selected(self, monkeypatch):
        app, fake = self._app(monkeypatch, [_order(42, "Client Z", bottles=12)])
        _type(app, "Client Z")
        assert not app.exception
        assert fake.search_texts == ["Client Z"]
        assert _selected(app) == [42]
        options = app.multiselect(key="baqio_selected").options
        assert any(o.startswith("#42 ") for o in options)
        assert any(o.startswith("#1 ") for o in options)
        assert fake.recent_calls == 1
        assert app.session_state.bottle == 12

    def test_exact_number_among_several(self, monkeypatch):
        found = [_order(420, "Client Y", bottles=6), _order(42, "Client Z", bottles=6)]
        app, _ = self._app(monkeypatch, found)
        _type(app, "#42")
        assert not app.exception
        assert _selected(app) == [42]
        assert len(app.multiselect(key="baqio_selected").options) == 3

    @pytest.mark.parametrize("text", ["42", "#42", "  #42  "])
    def test_exact_number_hash_optional(self, monkeypatch, text):
        found = [_order(420, "Client Y", bottles=6), _order(42, "Client Z", bottles=6)]
        app, _ = self._app(monkeypatch, found)
        _type(app, text)
        assert _selected(app) == [42]

    def test_exact_number_case_insensitive(self, monkeypatch):
        order = _order(42, "Client Z", bottles=6)
        order["name"] = "#ABC42"
        found = [order, _order(43, "Client Y", bottles=6)]
        app, _ = self._app(monkeypatch, found)
        _type(app, "abc42")
        assert _selected(app) == [42]

    def test_several_without_exact_match(self, monkeypatch):
        found = [_order(41, "Dupont A", bottles=6), _order(42, "Dupont B", bottles=6)]
        app, _ = self._app(monkeypatch, found)
        _type(app, "Dupont")
        assert not app.exception
        assert _selected(app) == []
        options = app.multiselect(key="baqio_selected").options
        assert any(o.startswith("#41 ") for o in options)
        assert any(o.startswith("#42 ") for o in options)
        message = baqio_app.MSG_SEARCH_CHOOSE.format(count=2, text="Dupont")
        assert message in _texts(app.info)

    def test_no_result(self, monkeypatch):
        app, fake = self._app(monkeypatch, [])
        _type(app, "inconnu")
        assert not app.exception
        assert fake.search_texts == ["inconnu"]
        assert _selected(app) == []
        message = baqio_app.MSG_SEARCH_NO_RESULT.format(text="inconnu")
        assert message in _texts(app.info)
        assert len(app.multiselect(key="baqio_selected").options) == 1

    @pytest.mark.parametrize(
        "error, message",
        [
            (BaqioAuthError("no"), baqio_app.MSG_AUTH),
            (BaqioUnavailableError("down"), baqio_app.MSG_UNAVAILABLE),
        ],
    )
    def test_errors(self, monkeypatch, error, message):
        app, _ = self._app(monkeypatch, [], search_raises=error)
        _type(app, "whatever")
        assert not app.exception
        assert _selected(app) == []
        assert message in _texts(app.error) + _texts(app.warning)
        app.number_input(key="bottle").set_value(7).run()
        assert not app.exception

    def test_typed_text_never_stays_selected(self, monkeypatch):
        app, _ = self._app(monkeypatch, [_order(42, "Client Z", bottles=6)])
        _type(app, "Client Z")
        assert all(isinstance(i, int) for i in _selected(app))
        assert "Client Z" not in app.multiselect(key="baqio_selected").values

    def test_existing_selection_kept(self, monkeypatch):
        app, _ = self._app(monkeypatch, [_order(42, "Client Z", bottles=6)])
        _select(app, [1])
        _type(app, "Client Z")
        assert not app.exception
        assert sorted(_selected(app)) == [1, 42]

    def test_existing_selection_kept_when_nothing_found(self, monkeypatch):
        app, _ = self._app(monkeypatch, [])
        _select(app, [1])
        _type(app, "inconnu")
        assert _selected(app) == [1]

    @pytest.mark.parametrize("text", ["", "   "])
    def test_blank_text_ignored(self, monkeypatch, text):
        app, fake = self._app(monkeypatch, [_order(42, "Client Z", bottles=6)])
        _select(app, [1])
        _type(app, text)
        assert not app.exception
        assert fake.search_texts == []
        assert _selected(app) == [1]
        assert baqio_app.MSG_SEARCH_NO_RESULT.format(text=text) not in _texts(app.info)

    def test_found_orders_validated_like_preload(self, monkeypatch):
        invoiced = _order(42, "Client Z", bottles=6)
        invoiced["state"] = "invoiced"
        bad_date = _order(43, "Client Y", bottles=6)
        bad_date["created_at"] = "pas une date"
        app, _ = self._app(monkeypatch, [invoiced, bad_date])
        _type(app, "Client")
        assert not app.exception
        assert _selected(app) == []
        assert len(app.multiselect(key="baqio_selected").options) == 1
        assert baqio_app.MSG_INVALID_ORDER.format(order="#43") in _texts(app.warning)

    def test_found_order_already_listed_not_duplicated(self, monkeypatch):
        app, _ = self._app(monkeypatch, [_order(1, "Client A", bottles=6)])
        _type(app, "Client A")
        assert _selected(app) == [1]
        assert len(app.multiselect(key="baqio_selected").options) == 1


class TestBaqioCatalog:
    """Product catalogue preloaded in a background thread (real thread in AppTest)."""

    @staticmethod
    def _started(fake):
        assert fake.catalog_started.wait(timeout=5)

    def test_constant(self):
        assert baqio_app.CATALOG_TIMEOUT == 10

    def test_catalog_requested_once_at_preload(self, monkeypatch):
        fake = FakeBaqioClient([[_order(1, "Client A", bottles=6)]], catalog={})
        app = _baqio_app(monkeypatch, fake)
        self._started(fake)
        app.run()
        _select(app, [1])
        assert fake.catalog_calls == 1

    def test_catalog_not_requested_when_preload_fails(self, monkeypatch):
        fake = FakeBaqioClient(raises=BaqioUnavailableError("down"))
        _baqio_app(monkeypatch, fake)
        assert not fake.catalog_started.wait(timeout=0.3)
        assert fake.catalog_calls == 0

    def test_catalog_hit_means_no_unit_call(self, monkeypatch):
        order = _order(1, "Client A", bottles=24, magnums=3)
        fake = FakeBaqioClient([[order]], catalog=dict(BAQIO_VARIANTS))
        app = _baqio_app(monkeypatch, fake)
        _select(app, [1])
        assert not app.exception
        assert app.session_state.bottle == 24
        assert app.session_state.magnum == 3
        assert fake.variant_calls == []

    def test_catalog_integrated_then_dropped(self, monkeypatch):
        order = _order(1, "Client A", bottles=6)
        fake = FakeBaqioClient([[order]], catalog=dict(BAQIO_VARIANTS))
        app = _baqio_app(monkeypatch, fake)
        _select(app, [1])
        assert app.session_state["baqio_catalog"] is None
        assert set(BAQIO_VARIANTS) <= set(app.session_state.baqio_variants)

    def test_variant_missing_from_catalog_single_unit_call(self, monkeypatch):
        order = _order(1, "Client A", bottles=24, magnums=3)
        fake = FakeBaqioClient(
            [[order]], catalog={BOTTLE_VARIANT: BAQIO_VARIANTS[BOTTLE_VARIANT]}
        )
        app = _baqio_app(monkeypatch, fake)
        _select(app, [1])
        assert not app.exception
        assert app.session_state.bottle == 24
        assert app.session_state.magnum == 3
        assert fake.variant_calls == [MAGNUM_VARIANT]

    @pytest.mark.parametrize(
        "error", [BaqioUnavailableError("down"), BaqioAuthError("bad"), ValueError()]
    )
    def test_catalog_error_falls_back_silently(self, monkeypatch, error):
        order = _order(1, "Client A", bottles=24, magnums=3)
        fake = FakeBaqioClient([[order]], catalog_raises=error)
        app = _baqio_app(monkeypatch, fake)
        _select(app, [1])
        assert not app.exception
        assert app.session_state.bottle == 24
        assert app.session_state.magnum == 3
        assert sorted(fake.variant_calls) == [BOTTLE_VARIANT, MAGNUM_VARIANT]
        assert _texts(app.error) == []
        assert baqio_app.MSG_UNAVAILABLE not in _texts(app.warning)
        assert baqio_app.MSG_AUTH not in _texts(app.error)
        assert app.session_state["baqio_catalog"] is None

    def test_refresh_restarts_catalog(self, monkeypatch):
        fake = FakeBaqioClient([[_order(1, "Client A", bottles=6)]])
        app = _baqio_app(monkeypatch, fake)
        self._started(fake)
        fake.catalog_started.clear()
        _refresh(app)
        self._started(fake)
        assert fake.catalog_calls == 2

    def test_slow_catalog_falls_back_and_is_kept(self, monkeypatch):
        monkeypatch.setattr(baqio_app, "CATALOG_TIMEOUT", 0.05)
        gate = threading.Event()
        order = _order(1, "Client A", bottles=24, magnums=3)
        fake = FakeBaqioClient(
            [[order]], catalog=dict(BAQIO_VARIANTS), catalog_gate=gate
        )
        try:
            app = _baqio_app(monkeypatch, fake)
            _select(app, [1])
            assert not app.exception
            assert app.session_state.bottle == 24
            assert sorted(fake.variant_calls) == [BOTTLE_VARIANT, MAGNUM_VARIANT]
            assert app.session_state["baqio_catalog"] is not None
            assert _texts(app.error) == []
        finally:
            gate.set()

    def test_slow_catalog_integrated_on_next_load(self, monkeypatch):
        monkeypatch.setattr(baqio_app, "CATALOG_TIMEOUT", 0.05)
        gate = threading.Event()
        first = _order(1, "Client A", bottles=6)
        second = _order(2, "Client B", bottles=12, magnums=2)
        catalog = {MAGNUM_VARIANT: BAQIO_VARIANTS[MAGNUM_VARIANT]}
        fake = FakeBaqioClient([[first, second]], catalog=catalog, catalog_gate=gate)
        try:
            app = _baqio_app(monkeypatch, fake)
            _select(app, [1])  # times out: unit call for the bottle variant
            assert fake.variant_calls == [BOTTLE_VARIANT]
            gate.set()
            monkeypatch.setattr(baqio_app, "CATALOG_TIMEOUT", 5)
            _select(app, [1, 2])  # catalogue now integrated: magnum needs no call
            assert not app.exception
            assert app.session_state.magnum == 2
            assert fake.variant_calls == [BOTTLE_VARIANT]
            assert app.session_state["baqio_catalog"] is None
        finally:
            gate.set()
