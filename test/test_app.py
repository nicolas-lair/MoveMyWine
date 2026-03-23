import pandas as pd
from streamlit.testing.v1 import AppTest

from src import streamlit_utils
from src.app_generics.fetched_indicator import FetchedIndicator
from src.app_generics.postal_code import PostalCodeAPI
from src.cost_calculator import CostType
from src.my_transporters.chronopost import app_calculator as chronopost_app
from src.my_transporters.geodis import app_calculator as geodis_app
from src.my_transporters.stef import app_calculator as stef_app
from src.streamlit_utils import TRANSPORTER_LIST


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
        for x in geodis_app.TransporterParams.modulators.values()
        if x.modulation_link == url
    ]
    return FetchedIndicator(
        retrieved=True, valid_date=True, value=default_val[0].default
    )


def mock_postal_code_retriever():
    return pd.DataFrame.from_dict(
        {
            "full_name": ["75017 - Paris 17", "69001 - Lyon 01", "49100 - Angers"],
            PostalCodeAPI.Cols.postal_code: ["75017", "69001", "49100"],
        },
    ).set_index("full_name")


def test_app(monkeypatch):
    monkeypatch.setattr(chronopost_app, "scrap_indicator", mock_chronopost_indicator)
    monkeypatch.setattr(stef_app, "scrap_indicator", mock_stef_indicator)
    monkeypatch.setattr(geodis_app, "scrap_indicator", mock_geodis_indicator)
    monkeypatch.setattr(
        streamlit_utils, "retrieve_postal_code", mock_postal_code_retriever
    )
    app = AppTest.from_file("../src/streamlit_app.py").run()

    assert not app.exception
    assert app.selectbox(key="transporter").value.params.name == "Stef"
    assert app.selectbox(key="destination").value == "75017 - Paris 17"
    app.number_input(key="stef_gnr_modulator").set_value(1.0).run()

    assert app.session_state.cost == 0

    ###################################################
    ##### STEF
    ###################################################

    app.number_input(key="bottle").set_value(24).run()
    assert app.session_state.detail_cost == {
        CostType.ByBottle: 41.68,  # Paris Tarif 1
        CostType.Palet: 1.0,
        CostType.Security: 0.7,
        CostType.Expedition: 5.41,
        CostType.GNRMod: 0.0,
        CostType.ColdMod: 0.0,
    }

    app.number_input(key="stef_gnr_modulator").set_value(1.42).run()
    assert app.session_state.detail_cost == {
        CostType.ByBottle: 41.68,  # Paris Tarif 1
        CostType.Palet: 1.0,
        CostType.Security: 0.7,
        CostType.Expedition: 5.41,
        CostType.GNRMod: 5.18,
        CostType.ColdMod: 0.0,
    }

    app.number_input(key="stef_froid_modulator").set_value(330).run()
    assert app.session_state.detail_cost == {
        CostType.ByBottle: 41.68,  # Paris Tarif 1
        CostType.Palet: 1.0,
        CostType.Security: 0.7,
        CostType.Expedition: 5.41,
        CostType.GNRMod: 5.18,
        CostType.ColdMod: 0.24,
    }

    ###################################################
    ##### GEODIS
    ###################################################

    app.selectbox(key="transporter").set_value(TRANSPORTER_LIST[1]).run()
    assert app.session_state.transporter.params.name == "Geodis"
    assert app.session_state.detail_cost == {
        CostType.ByBottle: 37.22,  # Zone 4 24 bouteilles
        CostType.Expedition: 2.2,
        CostType.GNRMod: 0,
        CostType.ByDestination: 3.4,
    }

    app.number_input(key="geodis_gnr_modulator").set_value(10).run()
    assert app.session_state.detail_cost == {
        CostType.ByBottle: 37.22,  # Zone 4 24 bouteilles
        CostType.Expedition: 2.2,
        CostType.GNRMod: 4.28,
        CostType.ByDestination: 3.4,
    }

    n_bottle = 97
    app.number_input(key="bottle").set_value(n_bottle).run()
    app.selectbox(key="destination").set_value("69001 - Lyon 01").run()
    assert app.session_state.detail_cost == {
        CostType.ByBottle: round(0.81 * n_bottle, 2),  # Zone 5 97 bouteilles
        CostType.Expedition: 2.2,
        CostType.GNRMod: round(0.1 * (0.81 * n_bottle + 2.2 + 10.4), 2),
        CostType.ByDestination: 10.4,
    }

    ###################################################
    ##### CHRONOPOST
    ###################################################
    app.selectbox(key="destination").set_value("75017 - Paris 17").run()
    app.number_input(key="bottle").set_value(24).run()
    app.selectbox(key="transporter").set_value(TRANSPORTER_LIST[2]).run()
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

    app.number_input(key="stef_gnr_modulator").set_value(1.0).run()
    app.number_input(key="stef_froid_modulator").set_value(300.0).run()
    app.number_input(key="bottle").set_value(36).run()
    assert app.session_state.detail_cost == {
        CostType.ByBottle: 41.68,  # Paris Tarif 1
        CostType.Palet: 1.0,
        CostType.Security: 0.7,
        CostType.Expedition: 5.41,
        CostType.GNRMod: 0,
        CostType.ColdMod: 0.0,
    }

    app.number_input(key="bottle").set_value(48).run()
    assert app.session_state.detail_cost == {
        CostType.ByBottle: 54.05,  # Paris Tarif 2
        CostType.Palet: 1.0,
        CostType.Security: 0.7,
        CostType.Expedition: 5.41,
        CostType.GNRMod: 0,
        CostType.ColdMod: 0.0,
    }

    app.selectbox(key="destination").set_value("69001 - Lyon 01").run()
    assert app.session_state.detail_cost == {
        CostType.ByBottle: 56.14,  # Lyon Tarif 2
        CostType.Palet: 1.0,
        CostType.Security: 0.7,
        CostType.Expedition: 5.41,
        CostType.GNRMod: 0,
        CostType.ColdMod: 0.0,
    }

    app.number_input(key="bottle").set_value(130).run()
    assert app.session_state.detail_cost == {
        # 0.77 = Price per bottle for 130 bottles to Lyon (69)
        CostType.ByBottle: round(0.77 * 130, 2),
        CostType.Palet: 1.0,
        CostType.Security: 0.7,
        CostType.Expedition: 5.41,
        CostType.GNRMod: 0,
        CostType.ColdMod: 0.0,
    }

    app.number_input(key="bottle").set_value(170).run()
    app.selectbox(key="destination").set_value("49100 - Angers").run()
    assert app.session_state.detail_cost == {
        # 0.38 = Price per bottle for 170 bottles to Angers (49)
        CostType.ByBottle: round(170 * 0.38, 2),
        CostType.Palet: 1.0,
        CostType.Security: 0.7,
        CostType.Expedition: 5.41,
        CostType.GNRMod: 0.0,
        CostType.ColdMod: 0.0,
    }
