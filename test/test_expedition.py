import pytest

from srcv2.constant import BaseBottle, Package
from srcv2.cost_calculator.expedition import SingleRefExpedition, MultiRefExpedition


class TestSingleRefExpedition:
    expe_without_package = SingleRefExpedition(bottle_type=BaseBottle(empty_weight=0.5, volume=0.75), n_bottles=3)
    package = Package(box_weight=1, bottle_by_package=6)
    expe_with_package = SingleRefExpedition(
        bottle_type=BaseBottle(empty_weight=0.5, volume=0.75), n_bottles=3, package=package)
    other_expe_with_package = SingleRefExpedition(
        bottle_type=BaseBottle(empty_weight=1, volume=1.5), n_bottles=12, package=package)

    def test_missing_package(self):
        with pytest.raises(AssertionError):
            _ = self.expe_without_package.n_package

        with pytest.raises(AssertionError):
            _ = self.expe_without_package.weight

    def test_n_package(self):
        self.expe_with_package.add_package_type(self.package)
        assert self.expe_with_package.n_package == 1
        assert self.other_expe_with_package.n_package == 2

    def test_weight(self):
        assert self.expe_with_package.weight == 3*(0.5+0.75) + 1
        assert self.other_expe_with_package.weight == 12*(1.5+1) + 2

    def test_bottle_eq(self):
        assert self.expe_with_package.n_bottles_equivalent == 3
        assert self.other_expe_with_package.n_bottles_equivalent == 24


class TestMultiRefExpedition:
    first_package = Package(box_weight=1, bottle_by_package=6)
    first_expe = SingleRefExpedition(
        bottle_type=BaseBottle(empty_weight=0.5, volume=0.75), n_bottles=3, package=first_package)

    second_package = Package(box_weight=2, bottle_by_package=3)
    second_expe = SingleRefExpedition(
        bottle_type=BaseBottle(empty_weight=1, volume=1), n_bottles=12)
    second_expe.add_package_type(second_package)

    def test_add_ref(self):
        expe = MultiRefExpedition([self.first_expe])
        assert len(expe) == 1
        expe.add_ref(self.second_expe)
        assert len(expe) == 2

    def test_n_packages(self):
        expe = MultiRefExpedition([self.first_expe, self.second_expe])
        assert expe.n_packages == self.first_expe.n_package + self.second_expe.n_package

    def test_weight(self):
        expe = MultiRefExpedition([self.first_expe, self.second_expe])
        assert expe.weight == self.first_expe.weight + self.second_expe.weight

    def test_bottle_eq(self):
        expe = MultiRefExpedition([self.first_expe, self.second_expe])
        assert expe.n_bottles_equivalent == self.first_expe.n_bottles_equivalent + self.second_expe.n_bottles_equivalent
