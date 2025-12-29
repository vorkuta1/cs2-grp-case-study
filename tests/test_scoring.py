import datetime
from decimal import Decimal

from cs2_arb.models import Listing, MarketFee
from cs2_arb.scoring.opportunity import ScoreConfig, opportunity_score


def test_opportunity_score_basics():
    # GRP (Model Price) = 150
    # Ask = 100
    # Edge should be 50%

    listing = Listing(
        market="test",
        listing_id="1",
        item_key="k",
        currency="USD",
        ask=Decimal("100.00"),
        ts=datetime.datetime.now(datetime.UTC),
        age_seconds=0,
    )

    ref_price = Decimal("150.00")
    ecb_rates = {"USD": Decimal("1.0")}  # Simplest case
    fee = MarketFee(pct=0.0)
    cfg = ScoreConfig(base_ccy="USD")

    score = opportunity_score(
        listing=listing, reference_price_usd=ref_price, ecb_rates=ecb_rates, fee=fee, cfg=cfg
    )

    # Score = Edge * H_liq * H_lock * H_risk
    # Edge = (150 - 100) / 100 = 0.50
    # H_liq (age=0) = 1.0
    # H_risk (penalty=0) = 1.0

    assert abs(score - Decimal("0.50")) < Decimal("0.001")


def test_liquidity_decay():
    # Old listing should have lower score
    listing_old = Listing(
        market="test",
        listing_id="1",
        item_key="k",
        currency="USD",
        ask=Decimal("100.00"),
        ts=datetime.datetime.now(datetime.UTC),
        age_seconds=3600 * 24 * 30,  # 30 days old
    )

    ref_price = Decimal("150.00")
    ecb_rates = {"USD": Decimal("1.0")}
    fee = MarketFee(pct=0.0)
    cfg = ScoreConfig(base_ccy="USD", tau_sell_seconds=3600 * 24)  # 1 day tau

    score = opportunity_score(
        listing=listing_old, reference_price_usd=ref_price, ecb_rates=ecb_rates, fee=fee, cfg=cfg
    )

    # H_liq should be very small (~e^-30)
    assert score < Decimal("0.01")
