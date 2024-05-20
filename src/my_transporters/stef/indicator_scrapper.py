from bs4 import BeautifulSoup
import requests
from datetime import date
from dateutil.relativedelta import relativedelta
from loguru import logger

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

        last_value_info = soup.find(id="lastValue").get_text()
        year_month, indicator = [c.strip() for c in last_value_info.split(":")]
        last_month = (date.today() - relativedelta(months=1)).strftime("%Y-%m")
        valid_date = last_month == year_month
        indicator = float(indicator.replace(",", "."))

        return FetchedIndicator(retrieved=True, valid_date=valid_date, value=indicator)
    except Exception as e:
        logger.info(f"Error retrieving gas modulation: {e}", feature="f-strings")
        return FetchedIndicator(retrieved=False)
