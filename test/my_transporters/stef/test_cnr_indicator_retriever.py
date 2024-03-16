from srcv2.my_transporters.stef.gas_modulation_indicator import retrieve_indicator


class TestCNRIndicatorRetriever:
    def test_retrieve_indicator(self):
        success, valid_date, indicator = retrieve_indicator()
        assert success
        assert isinstance(valid_date, bool)
        assert isinstance(indicator, float)

    def test_failed_retrieval(self):
        fail, valid_date, indicator = retrieve_indicator(url="dummy_url")
        assert not fail
        assert indicator == 1.0
        assert valid_date is None
