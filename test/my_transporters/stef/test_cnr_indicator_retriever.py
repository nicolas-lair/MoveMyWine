from srcv2.my_transporters.stef.gas_modulation_indicator import retrieve_indicator


class TestCNRIndicatorRetriever:
    def test_retrieve_indicator(self):
        valid_date, indicator = retrieve_indicator()
        assert indicator is not None
        assert isinstance(valid_date, bool)
        assert isinstance(indicator, float)

        valid_date, indicator = retrieve_indicator(url="dummy_url")
        assert indicator is None
        assert valid_date is None
