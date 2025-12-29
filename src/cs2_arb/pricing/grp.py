from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from cs2_arb.fx.ecb import convert
from cs2_arb.models import MarketFee, PricePrint
from cs2_arb.pricing.fees import net_proceeds
from cs2_arb.util.weighted import weighted_median


@dataclass(frozen=True)
class GRPConfig:
    base_ccy: str = "USD"
    tau_seconds: float = 3600.0
    epsilon_spread: float = 1e-6


def _time_decay(ts: datetime, now: datetime, tau: float) -> float:
    import math

    age = max(0.0, (now - ts).total_seconds())
    return float(math.exp(-age / tau))


def grp_for_item(
    *,
    prints: Iterable[PricePrint],
    ecb_rates: dict[str, Decimal],
    fees_by_market: dict[str, MarketFee],
    cfg: GRPConfig,
    now: datetime | None = None,
) -> Decimal:
    now = now or datetime.now(UTC)
    vals: list[tuple[Decimal, float]] = []

    for p in prints:
        fee = fees_by_market.get(p.market, MarketFee(pct=0.0))
        net = net_proceeds(p.price, fee)
        px = convert(net, p.currency, cfg.base_ccy, ecb_rates)

        vol = (p.volume_7d or 1.0) ** 0.5
        td = _time_decay(p.ts, now, cfg.tau_seconds)
        spr = float(p.spread) if p.spread is not None else 0.02
        w = float(vol * td / (spr + cfg.epsilon_spread))
        vals.append((px, w))

    if not vals:
        raise ValueError("No prints provided")
    return weighted_median(vals)
