from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ManufacturingConfig:
    input_count: int = 10
    default_input_count: int = 10
    covert_input_count: int = 5

    ops_cost: Decimal = Decimal("0.0")  # Operational cost per contract


def calculate_input_cost(
    input_grp_prices: Iterable[Decimal],
    input_rarity: str = "Mil-Spec",  # Default usually implies 10
    ops_cost: Decimal = Decimal("0"),
) -> Decimal:
    """
    Cost_in = count * wMedian(GRP(inputs)) + Costs_ops

    Rules:
    - Covert inputs (for Knife/Gold): 5 inputs
    - All others: 10 inputs
    """
    count = 10
    if input_rarity.lower() == "covert":
        count = 5

    prices = list(input_grp_prices)
    if not prices:
        return Decimal("0")

    sorted_p = sorted(prices)
    mid = len(sorted_p) // 2
    if len(sorted_p) % 2 == 1:
        representative_price = sorted_p[mid]
    else:
        representative_price = (sorted_p[mid - 1] + sorted_p[mid]) / Decimal("2")

    return Decimal(count) * representative_price + ops_cost


def calculate_output_ev(
    outputs: list[tuple[Decimal, float]],  # (price, probability)
) -> Decimal:
    """
    EV_out = sum(p_g * P_GRP(g))
    """
    ev = Decimal("0")
    total_prob = 0.0
    for price, prob in outputs:
        ev += price * Decimal(str(prob))
        total_prob += prob

    if total_prob == 0:
        return Decimal("0")

    # Normalize if probs don't sum to 1.0
    if not (0.99 <= total_prob <= 1.01):
        ev = ev / Decimal(str(total_prob))

    return ev


def manufacturing_edge(input_cost: Decimal, output_ev: Decimal) -> Decimal:
    """
    Edge = EV_out - Cost_in
    """
    return output_ev - input_cost
