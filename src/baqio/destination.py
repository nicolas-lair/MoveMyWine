import re
import unicodedata
from dataclasses import dataclass

import pandas as pd

from src.app_generics.postal_code import PostalCodeAPI

MSG_NO_ADDRESS = "Adresse de livraison absente — destination inchangée."
MSG_NOT_FRANCE = "Adresse hors de France ({country}) — destination inchangée."
MSG_ZIP_NOT_FOUND = "Code postal {zip} introuvable — destination inchangée."
MSG_CITY_NOT_FOUND = (
    "Commune « {city} » introuvable pour le code postal {zip} "
    "— « {key} » retenue, à vérifier."
)


@dataclass(frozen=True)
class DestinationMatch:
    key: str | None  # index de df_postal_code ; None = destination inchangée
    warning: str | None


def normalize_city(name: str) -> str:
    decomposed = unicodedata.normalize("NFKD", name)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    spaced = stripped.upper().replace("-", " ").replace("'", " ")
    return re.sub(r"\s+", " ", spaced).strip()


def postal_code_of(key: str) -> str:
    """Destination entries read "CP - Commune[ - Lieu-dit]"."""
    return key.split(" - ")[0].strip()


def match_destination(
    df_postal_code: pd.DataFrame,
    zip: str | None,
    city: str | None,
    country: str | None,
) -> DestinationMatch:
    cols = PostalCodeAPI.Cols
    zip = (zip or "").strip()
    if not zip:
        return DestinationMatch(None, MSG_NO_ADDRESS)
    if country and country.strip().upper() != "FR":
        return DestinationMatch(None, MSG_NOT_FRANCE.format(country=country))

    rows = df_postal_code[df_postal_code.index.map(postal_code_of) == zip]
    if rows.empty:
        return DestinationMatch(None, MSG_ZIP_NOT_FOUND.format(zip=zip))

    if rows[cols.commune].nunique() > 1:
        wanted = normalize_city(city or "")
        same_city = rows[
            rows[cols.commune].map(lambda c: normalize_city(str(c))) == wanted
        ]
        if same_city.empty:
            key = rows.index[0]
            return DestinationMatch(
                key, MSG_CITY_NOT_FOUND.format(city=city or "", zip=zip, key=key)
            )
        rows = same_city

    no_lieudit = rows[rows[cols.lieudit].fillna("") == ""]
    return DestinationMatch((no_lieudit if len(no_lieudit) else rows).index[0], None)
