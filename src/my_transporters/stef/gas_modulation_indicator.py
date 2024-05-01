from bs4 import BeautifulSoup
import requests
from datetime import date
from dateutil.relativedelta import relativedelta
from loguru import logger
import streamlit as st

from .constant import TransporterParams


@st.cache_data
def retrieve_indicator(
    url=TransporterParams.gas_modulation_link
) -> (bool, bool, float):
    return _retrieve_indicator(url=url)


def _retrieve_indicator(
    url=TransporterParams.gas_modulation_link
) -> (bool, bool, float):
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

        return True, valid_date, indicator
    except Exception as e:
        logger.info(f"Error retrieving gas modulation: {e}", feature="f-strings")
        return False, None, 1.0
