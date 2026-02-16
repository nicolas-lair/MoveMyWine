import re
from datetime import date

import requests
from babel.dates import format_date
from bs4 import BeautifulSoup
from loguru import logger

from src.app_generics.fetched_indicator import FetchedIndicator


def scrap_indicator(url: str) -> FetchedIndicator:
    """
    Retrieve the gas modulation input value from the Geodis website

    Return
        success: bool, indicate that the indicator successfully retrieved
        valid_date: bool, date of the last indicator should be last month
        indicator: float, value of the indicator
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.8,en-US;q=0.6,en;q=0.4",
    }

    try:
        response = requests.get(url, verify=False, headers=headers)
        assert response.status_code == 200
        soup = BeautifulSoup(response.text, "html.parser")

        for p in soup.find_all("p"):
            if "Taux général" in p.get_text():
                month_year, rate = re.findall(
                    r"Taux général (?P<date>.*?): (?P<taux>[\d,]+\.\d+)%", p.get_text()
                )[0]

                valid_date = (
                    format_date(date.today(), format="MMMM Y", locale="fr")
                    == month_year
                )
                gas_factor = float(rate)

                return FetchedIndicator(
                    retrieved=True, valid_date=valid_date, value=gas_factor
                )
        return FetchedIndicator(retrieved=False)
    except Exception as e:
        logger.info(f"Error retrieving gas modulation: {e}", feature="f-strings")
