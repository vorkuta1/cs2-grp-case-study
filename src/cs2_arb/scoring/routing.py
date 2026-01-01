from __future__ import annotations

import math
from decimal import Decimal

from cs2_arb.models import Listing, Route
from cs2_arb.pricing.normalization import buy_cost, normalize_currency, sell_proceeds
from cs2_arb.venue import VenueModel

# Hyperparameters (could be moved to settings)
TAU_SELL = 7.0  # Days to sell
RATE_CARRY = 0.05 / 365.0  # Daily cost of capital (5% annual)
KAPPA_RISK = 1.0


def score_route(
    listing: Listing,
    buy_venue: VenueModel,
    sell_venue: VenueModel,
    sell_price_local: Decimal,  # Price in Sell Venue's currency
    ecb_rates: dict[str, Decimal],
    implied_rates: dict[tuple[str, str], Decimal] | None = None,
) -> Route:
    """
    Computes the route score for buying at `listing` (on buy_venue)
    and selling at `sell_price_local` (on sell_venue).
    """

    # 1. Calculate Buy Cost in USD (Cash)
    #    Cost in listing currency -> USD Cash
    cost_native = buy_cost(listing.ask, buy_venue)
    cost_usd = normalize_currency(
        cost_native, listing.currency, "USD", ecb_rates, implied_rates, rail_friction=0.0
    )

    # 2. Calculate Sell Proceeds in USD (Cash)
    #    Proceeds in exit currency -> USD Cash
    proceeds_native = sell_proceeds(sell_price_local, sell_venue)

    # If Selling on a venue with restricted currency (e.g. Steam Wallet),
    # and we want "USD Cash" out, we need to price the "Cash out" rail.
    # We simulate this by checking if venue.currency != "USD_cash" (or derived).
    # For now, we assume normalize_currency handles the rail friction if we ask for USD.

    # We assume 'USD' implies USD Cash.
    proceeds_usd = normalize_currency(
        proceeds_native, sell_venue.currency, "USD", ecb_rates, implied_rates, rail_friction=0.02
    )

    # 3. Edge
    edge_raw = -1.0 if cost_usd == 0 else float((proceeds_usd - cost_usd) / cost_usd)

    # 4. Haircuts

    # Liquidity: Time to sell
    # Heuristic: If we have volume data, use it. Else assume default.
    # We don't have volume in the generic call here, defaulting to TAU_SELL.
    # In a real system, we'd estimate TTS based on demand.
    tts_est = 3.0  # placeholder
    liquidity_haircut = math.exp(-tts_est / TAU_SELL)

    # Lockup: Settlement days
    lock_days = buy_venue.settlement_days + sell_venue.settlement_days
    lockup_haircut = math.exp(-lock_days * RATE_CARRY)

    # Risk: Venue trust
    risk_haircut = 1.0 - sell_venue.risk_score

    # 5. Final Score
    # Score = Edge * H_liq * H_lock * H_risk
    # If edge is negative, haircuts define how "clean" the loss is (makes less sense),
    # usually we care about positive edge.
    # We preserve the sign of the edge.

    score = edge_raw * liquidity_haircut * lockup_haircut * risk_haircut

    return Route(
        listing_id=listing.listing_id,
        item_key=listing.item_key,
        buy_venue=buy_venue.name,
        sell_venue=sell_venue.name,
        buy_cost_usd=cost_usd,
        sell_proceeds_usd=proceeds_usd,
        edge_raw=edge_raw,
        roi_pct=edge_raw * 100.0,
        liquidity_haircut=liquidity_haircut,
        lockup_haircut=lockup_haircut,
        risk_haircut=risk_haircut,
        score=score,
    )
