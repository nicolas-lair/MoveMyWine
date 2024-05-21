from io import StringIO
import requests
from datetime import date

from bs4 import BeautifulSoup
from loguru import logger
from babel.dates import format_date

import pandas as pd

from src.app_generics.fetched_indicator import FetchedIndicator


def scrap_indicator(url: str) -> FetchedIndicator:
    """
    Retrieve the gas modulation input value from the CNR website

    Return
        success: bool, indicate that the indicator successfully retrieved
        valid_date: bool, date of the last indicator should be last month
        indicator: float, value of the indicator
    """
    try:
        response = requests.get(url)

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")
        df = pd.read_html(StringIO(str(table)), index_col=0)[0]

        valid_date = (
            format_date(date.today(), format="MMMM  Y", locale="fr")
            == df.columns[-1].lower()
        )
        assert (
            df.index[0]
            == "Routier Services concernés : Tous les produits nationaux et le Chrono Classic"
        )

        gas_factor = df.loc[df.index[0], df.columns[-1]]
        gas_factor = float(gas_factor[:-1])

        return FetchedIndicator(retrieved=True, valid_date=valid_date, value=gas_factor)
    except Exception as e:
        logger.info(f"Error retrieving gas modulation: {e}", feature="f-strings")
        return FetchedIndicator(retrieved=False)
