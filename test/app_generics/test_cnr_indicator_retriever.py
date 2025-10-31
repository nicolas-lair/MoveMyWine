import loguru
import pytest

from src.app_generics.scrap_cnr_indicator import scrap_indicator
from src.my_transporters.stef.constant import TransporterParams as StefParams
from src.my_transporters.kuehne_nagel.constant import TransporterParams as KNGParams


class TestCNRIndicatorRetriever:
    @pytest.mark.parametrize(
        "modulation_link",
        [
            StefParams.modulators["GNR"].modulation_link,
            StefParams.modulators["Froid"].modulation_link,
            KNGParams.modulators["GNR"].modulation_link,
        ],
    )
    def test_retrieve_indicator(self, modulation_link):
        indicator = scrap_indicator(modulation_link)
        assert indicator.retrieved
        assert isinstance(indicator.value, float)
        assert isinstance(indicator.valid_date, bool)

    def test_failed_retrieval(self):
        loguru.logger.remove()
        indicator = scrap_indicator(url="dummy_url")
        assert not indicator.retrieved
        assert indicator.value == 1.0
        assert not indicator.valid_date
