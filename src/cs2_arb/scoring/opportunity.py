from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from cs2_arb.fx.ecb import convert
from cs2_arb.models import Listing, MarketFee
from cs2_arb.pricing.fees import net_proceeds


@dataclass(frozen=True)
class ScoreConfig:
    base_ccy: str = "USD"
    tau_sell_seconds: float = 72 * 3600
    venue_risk_penalty: float = 0.0


def liquidity_haircut(age_seconds: int | None, tau: float) -> float:
    import math

    if age_seconds is None:
        return 1.0
    return float(math.exp(-max(0.0, age_seconds) / tau))


def opportunity_score(
    *,
    listing: Listing,
    reference_price_usd: Decimal,  # GRP or Model Price
    ecb_rates: dict[str, Decimal],
    fee: MarketFee,
    cfg: ScoreConfig,
    now: datetime | None = None,
) -> Decimal:
    """
    Score = Edge * H_liq * H_lock * H_risk - Penalty
    Edge is based on reference_price_usd (which should include feature adjustments if applied).
    """
    now = now or datetime.now(UTC)
    ask_net = net_proceeds(listing.ask, fee)
    ask_usd = convert(ask_net, listing.currency, cfg.base_ccy, ecb_rates)

    if ask_usd <= 0:
        return Decimal("-1")

    # Edge (net)
    edge = (reference_price_usd - ask_usd) / ask_usd

    # Haircuts
    h_liq = Decimal(str(liquidity_haircut(listing.age_seconds, cfg.tau_sell_seconds)))

    # Placeholder for lock/risk if we had them in Listing/Market
    h_lock = Decimal("1.0")
    h_risk = Decimal("1.0") - Decimal(str(cfg.venue_risk_penalty))

    score = edge * h_liq * h_lock * h_risk

    return score
