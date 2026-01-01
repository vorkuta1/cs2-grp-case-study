from decimal import Decimal

from cs2_arb.util.weighted import weighted_median


def test_weighted_median_basic() -> None:
    v = [(Decimal("1"), 1.0), (Decimal("2"), 1.0), (Decimal("3"), 1.0)]
    assert weighted_median(v) == Decimal("2")


def test_weighted_median_weights() -> None:
    v = [(Decimal("1"), 10.0), (Decimal("2"), 1.0), (Decimal("100"), 1.0)]
    assert weighted_median(v) == Decimal("1")
