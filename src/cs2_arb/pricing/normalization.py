from __future__ import annotations

from decimal import Decimal

from cs2_arb.fx.ecb import convert
from cs2_arb.venue import VenueModel


def buy_cost(price: Decimal, venue: VenueModel) -> Decimal:
    """
    Calculates the total cost to buy an item at the given price on the venue.
    This applies the BUY-side fees (buyer pays).
    """
    return venue.buy_fee.calculate_cost(price)


def sell_proceeds(price: Decimal, venue: VenueModel) -> Decimal:
    """
    Calculates the net proceeds from selling an item at the given price on the venue.
    This applies the SELL-side fees (seller pays).
    """
    return venue.sell_fee.calculate_proceeds(price)


def normalize_currency(
    amount: Decimal,
    source_ccy: str,
    target_ccy: str,
    ecb_rates: dict[str, Decimal],
    implied_rates: dict[tuple[str, str], Decimal] | None = None,
    rail_friction: float = 0.0,
) -> Decimal:
    """
    Converts amount from source_ccy to target_ccy using the best available rate.
    
    Priority:
    1. Implied FX (if available for the pair)
    2. ECB Spot Rate
    
    Then applies rail_friction (e.g. 0.02 for 2% conversion loss).
    """
    if source_ccy == target_ccy:
        converted = amount
    else:
        # 1. Try Implied FX
        if implied_rates:
            pair = (source_ccy, target_ccy)
            if pair in implied_rates:
                rate = implied_rates[pair]
                converted = amount * rate
                # Skip ECB Fallback if Implied found
            else:
                # 2. Fallback to ECB Spot
                converted = convert(amount, source_ccy, target_ccy, ecb_rates)
        else:
             # 2. Fallback to ECB Spot
            converted = convert(amount, source_ccy, target_ccy, ecb_rates)

    # Apply friction (only on cross-currency OR rail usage)
    # Effective Amount = Converted * (1 - friction)
    if rail_friction > 0:
        friction_mult = Decimal(str(1.0 - rail_friction))
        return converted * friction_mult
        
    return converted
