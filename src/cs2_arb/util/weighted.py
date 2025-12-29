from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal


def weighted_median(values: Iterable[tuple[Decimal, float]]) -> Decimal:
    """
    Weighted median for robust aggregation.

    Args:
        values: iterable of (value, weight) tuples. weights must be >=0 and not all 0.

    Returns:
        Decimal weighted median.
    """
    pairs: list[tuple[Decimal, float]] = [(v, float(w)) for v, w in values if float(w) > 0]
    if not pairs:
        raise ValueError("weighted_median requires at least one positive-weight value")

    pairs.sort(key=lambda x: x[0])
    total = sum(w for _, w in pairs)
    if total <= 0:
        raise ValueError("weighted_median requires total weight > 0")

    cum = 0.0
    for v, w in pairs:
        cum += w
        if cum >= total / 2:
            return v

    return pairs[-1][0]
