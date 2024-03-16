from bs4 import BeautifulSoup
import requests
from .constant import TransporterParams
from datetime import date
from dateutil.relativedelta import relativedelta
from loguru import logger


def retrieve_indicator(url=TransporterParams.gas_modulation_link) -> (bool, float):
    """
    Retrieve the gas modulation input value from the CNR website

    Return
        valid_date: bool, date of the last indicator should of last month
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

        return valid_date, indicator
    except Exception as e:
        logger.info(f"Error retrieving gas modulation: {e}", feature="f-strings")
        return None, None
