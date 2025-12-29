from decimal import Decimal

from cs2_arb.fx.ecb import convert


def test_convert_via_eur():
    rates = {"EUR": Decimal("1"), "USD": Decimal("2"), "CNY": Decimal("10")}
    assert convert(Decimal("1"), "USD", "CNY", rates) == Decimal("5")
