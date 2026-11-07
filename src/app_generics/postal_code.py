from enum import StrEnum

import pandas as pd


class PostalCodeAPI:
    # https://data.laposte.fr/datasets/laposte-hexasmal/api-doc
    # /raw serves the original CSV file: latin1, ";" separated, original column names
    endpoint = "https://data.laposte.fr/data-fair/api/v1/datasets/laposte-hexasmal/raw"

    class Cols(StrEnum):
        postal_code = "Code_postal"
        commune = "Nom_de_la_commune"
        lieudit = "Ligne_5"


def get_postal_code_df():
    col_enum = PostalCodeAPI.Cols
    df = pd.read_csv(
        PostalCodeAPI.endpoint,
        encoding="latin1",
        sep=";",
        usecols=[c.value for c in col_enum],
        dtype=str,
    )
    df = df.drop_duplicates(keep="first")
    df[col_enum.commune] = df[col_enum.commune].str.title()
    df[col_enum.lieudit] = df[col_enum.lieudit].str.title()
    # Vectorized concat (a row-wise apply takes > 1 s on the ~39k rows)
    df["full_name"] = (
        df[col_enum.postal_code]
        + " - "
        + df[col_enum.commune]
        + (" - " + df[col_enum.lieudit]).fillna("")
    )
    return df.set_index("full_name")
