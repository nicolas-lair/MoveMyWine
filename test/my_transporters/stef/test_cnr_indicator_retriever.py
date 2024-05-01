import loguru

from src.my_transporters.stef.gas_modulation_indicator import scrap_indicator


class TestCNRIndicatorRetriever:
    def test_retrieve_indicator(self):
        success, valid_date, indicator = scrap_indicator()
        assert success
        assert isinstance(valid_date, bool)
        assert isinstance(indicator, float)

    def test_failed_retrieval(self):
        loguru.logger.remove()
        fail, valid_date, indicator = scrap_indicator(url="dummy_url")
        assert not fail
        assert indicator == 1.0
        assert valid_date is None
