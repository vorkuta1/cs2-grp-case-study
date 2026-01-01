import datetime
from decimal import Decimal

from cs2_arb.models import Listing
from cs2_arb.scoring.routing import score_route
from cs2_arb.venue import FeeStructure, VenueModel


def test_route_score_simple() -> None:
    # Buy @ 100 on Demo (0 fee)
    # Sell @ 150 on Steam (15% fee)
    # Edge = 150 * 0.85 = 127.5. (127.5 - 100) / 100 = 27.5%

    listing = Listing(
        listing_id="1",
        item_key="k",
        market="demo",
        currency="USD",
        ask=Decimal("100.00"),
        ts=datetime.datetime.now(datetime.UTC),
        age_seconds=0,
    )

    buy_venue = VenueModel(
        name="demo", currency="USD", buy_fee=FeeStructure(pct=0.0), sell_fee=FeeStructure(pct=0.02)
    )

    sell_venue = VenueModel(
        name="steam",
        currency="USD",
        buy_fee=FeeStructure(pct=0.0),  # Irrelevant for selling
        sell_fee=FeeStructure(pct=0.15),
        settlement_days=7,
    )

    ecb_rates = {"USD": Decimal("1.0")}

    route = score_route(
        listing=listing,
        buy_venue=buy_venue,
        sell_venue=sell_venue,
        sell_price_local=Decimal("150.00"),
        ecb_rates=ecb_rates,
    )

    # Check Net calculations
    # Buy Cost: 100 * 1.0 + 0 = 100.
    # Sell Proceeds: 150 * (1 - 0.15) = 127.5
    assert route.buy_cost_usd == Decimal("100.00")
    # Sell Proceeds: 150 * 0.85 = 127.5.
    # Plus 2% friction (hardcoded in routing.py for now as 'venue exit cost' proxy): 127.5 * 0.98 = 124.95
    assert route.sell_proceeds_usd == Decimal("124.95000")

    # Edge
    expected_edge = (Decimal("124.95") - Decimal("100")) / Decimal("100")
    assert abs(route.edge_raw - float(expected_edge)) < 1e-6

    # Score
    # Cuts: Liquidity (default 3 days / 7) = e^-0.428 ~ 0.65
    # Lockup: 7 days @ 5% annual = e^(-7 * 0.05/365) ~ e^-0.00095 ~ 0.999
    # Risk: 0
    assert route.score < route.edge_raw
    assert route.score > 0


def test_cross_currency_route() -> None:
    # Buy @ 1000 CNY (~140 USD)
    # Sell @ 160 USD
    # 1 USD = 7.0 CNY

    listing = Listing(
        listing_id="2",
        item_key="k2",
        market="buff",
        currency="CNY",
        ask=Decimal("1000.00"),
        ts=datetime.datetime.now(datetime.UTC),
    )

    buy_venue = VenueModel(
        name="buff", currency="CNY", buy_fee=FeeStructure(pct=0.0), sell_fee=FeeStructure(pct=0.02)
    )

    sell_venue = VenueModel(
        name="steam", currency="USD", buy_fee=FeeStructure(pct=0.0), sell_fee=FeeStructure(pct=0.15)
    )

    ecb_rates = {"USD": Decimal("1.1"), "CNY": Decimal("7.7")}
    # EUR/USD = 1.1, EUR/CNY = 7.7 => USD/CNY = 7.0

    route = score_route(
        listing=listing,
        buy_venue=buy_venue,
        sell_venue=sell_venue,
        sell_price_local=Decimal("160.00"),
        ecb_rates=ecb_rates,
    )

    # Buy Cost: 1000 CNY -> /7.7 * 1.1 = 142.857 USD
    cost_usd = (Decimal("1000") / Decimal("7.7")) * Decimal("1.1")
    assert abs(route.buy_cost_usd - cost_usd) < Decimal("0.001")

    # Sell Price: 160 USD -> 160 * 0.85 = 136 USD
    proceeds = Decimal("160") * Decimal("0.85")

    # Sell Venue is USD but restricted (implied 2% friction in code)
    # proceeds_usd = 136 * (1 - 0.02) = 133.28
    expected_proceeds = proceeds * Decimal("0.98")
    assert abs(route.sell_proceeds_usd - expected_proceeds) < Decimal("0.001")

    # Edge should be negative (133 vs 142)
    assert route.edge_raw < 0
