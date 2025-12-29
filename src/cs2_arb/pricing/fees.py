from __future__ import annotations

from decimal import Decimal

from cs2_arb.models import MarketFee


def net_proceeds(gross: Decimal, fee: MarketFee) -> Decimal:
    pct = Decimal(str(fee.pct))
    return (gross * (Decimal("1") - pct)) - fee.fixed
