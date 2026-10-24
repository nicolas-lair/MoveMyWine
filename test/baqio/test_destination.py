import numpy as np
import pandas as pd
import pytest

from src.baqio.destination import (
    MSG_CITY_NOT_FOUND,
    MSG_NO_ADDRESS,
    MSG_NOT_FRANCE,
    MSG_ZIP_NOT_FOUND,
    match_destination,
    normalize_city,
    postal_code_of,
)


def _build_df(rows):
    df = pd.DataFrame(
        rows, columns=["Code_postal", "Nom_de_la_commune", "Ligne_5"], dtype=object
    )
    df["full_name"] = df.apply(
        lambda r: " - ".join(v for v in r if isinstance(v, str) and v), axis=1
    )
    return df.set_index("full_name")


@pytest.fixture
def df_postal_code():
    return _build_df(
        [
            ("33950", "Lège-Cap-Ferret", "Claouey"),  # lieu-dit placed first
            ("33950", "Lège-Cap-Ferret", np.nan),
            ("33120", "Arcachon", np.nan),
            ("33260", "Cazaux", np.nan),
            ("33260", "La Teste-De-Buch", ""),
            ("38080", "L'Isle-D'Abeau", np.nan),
            ("75011", "Paris 11", np.nan),
        ]
    )


def test_normalize_city():
    assert normalize_city("Lège-Cap-Ferret") == normalize_city("LEGE CAP FERRET")
    assert normalize_city("L'Isle-d'Abeau") == "L ISLE D ABEAU"


def test_exact_match(df_postal_code):
    result = match_destination(df_postal_code, "33120", "ARCACHON", "FR")
    assert result.key == "33120 - Arcachon"
    assert result.warning is None


def test_prefers_entry_without_lieudit(df_postal_code):
    result = match_destination(df_postal_code, "33950", "LEGE-CAP-FERRET", "FR")
    assert result.key == "33950 - Lège-Cap-Ferret"
    assert result.warning is None


def test_several_communes_same_zip(df_postal_code):
    # Cazaux is listed before La Teste-De-Buch for 33260
    result = match_destination(df_postal_code, "33260", "La Teste-de-Buch", "FR")
    assert result.key == "33260 - La Teste-De-Buch"
    assert result.warning is None


def test_city_not_found(df_postal_code):
    result = match_destination(df_postal_code, "33260", "Inconnue", "FR")
    assert result.key == "33260 - Cazaux"
    assert result.warning == MSG_CITY_NOT_FOUND.format(
        city="Inconnue", zip="33260", key="33260 - Cazaux"
    )


def test_zip_not_found(df_postal_code):
    result = match_destination(df_postal_code, "99999", "Arcachon", "FR")
    assert result.key is None
    assert result.warning == MSG_ZIP_NOT_FOUND.format(zip="99999")


def test_not_france(df_postal_code):
    result = match_destination(df_postal_code, "33120", "Arcachon", "BE")
    assert result.key is None
    assert result.warning == MSG_NOT_FRANCE.format(country="BE")


def test_missing_zip(df_postal_code):
    result = match_destination(df_postal_code, None, "Arcachon", "FR")
    assert result.key is None
    assert result.warning == MSG_NO_ADDRESS


def test_country_none_treated_as_france(df_postal_code):
    result = match_destination(df_postal_code, "33120", "Arcachon", None)
    assert result.key == "33120 - Arcachon"
    assert result.warning is None


def test_single_commune_zip_ignores_city_name(df_postal_code):
    # Baqio says "Paris", the entry is "Paris 11": the zip alone decides
    result = match_destination(df_postal_code, "75011", "Paris", "FR")
    assert result.key == "75011 - Paris 11"
    assert result.warning is None


def test_single_commune_zip_with_unrelated_city(df_postal_code):
    result = match_destination(df_postal_code, "33120", "Nulle part", "FR")
    assert result.key == "33120 - Arcachon"
    assert result.warning is None


def test_single_commune_zip_without_city(df_postal_code):
    result = match_destination(df_postal_code, "75011", None, "FR")
    assert result.key == "75011 - Paris 11"
    assert result.warning is None


def test_several_communes_city_found_with_accents(df_postal_code):
    result = match_destination(df_postal_code, "33260", "LA TESTE DE BUCH", "FR")
    assert result.key == "33260 - La Teste-De-Buch"
    assert result.warning is None


def test_several_communes_city_missing_takes_first_with_warning(df_postal_code):
    result = match_destination(df_postal_code, "33260", None, "FR")
    assert result.key == "33260 - Cazaux"
    assert result.warning is not None


def test_postal_code_of():
    assert postal_code_of("75011 - Paris 11") == "75011"
    assert postal_code_of("33950 - Lège-Cap-Ferret - Claouey") == "33950"
    assert postal_code_of(" 33120 - Arcachon") == "33120"
    assert postal_code_of("33120") == "33120"
