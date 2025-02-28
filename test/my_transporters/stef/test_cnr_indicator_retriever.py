import loguru

from src.app_generics.scrap_cnr_indicator import scrap_indicator
from src.my_transporters.stef.constant import TransporterParams


class TestCNRIndicatorRetriever:
    def test_retrieve_indicator(self):
        indicator = scrap_indicator(TransporterParams.modulators["GNR"].modulation_link)
        assert indicator.retrieved
        assert isinstance(indicator.value, float)
        assert isinstance(indicator.valid_date, bool)

    def test_failed_retrieval(self):
        loguru.logger.remove()
        indicator = scrap_indicator(url="dummy_url")
        assert not indicator.retrieved
        assert indicator.value == 1.0
        assert not indicator.valid_date
