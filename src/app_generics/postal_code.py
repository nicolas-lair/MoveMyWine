from enum import StrEnum
import pandas as pd


class PostalCodeAPI:
    # https://datanova.laposte.fr/datasets/laposte-hexasmal/api-doc
    endpoint = (
        "https://datanova.laposte.fr/data-fair/api/v1/datasets/laposte-hexasmal/raw"
    )

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
    df["full_name"] = df[[c.value for c in col_enum]].apply(
        lambda c: c.str.cat(sep=" - "), axis=1
    )
    return df
