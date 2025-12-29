from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from cs2_arb.util.weighted import weighted_median


@dataclass(frozen=True)
class ImpliedFXResult:
    base_ccy: str
    quote_ccy: str
    implied_rate: Decimal
    n: int


def implied_fx(
    *,
    benchmark_pairs: Iterable[tuple[Decimal, Decimal, float]],
    base_ccy: str,
    quote_ccy: str,
) -> ImpliedFXResult:
    """
    Estimate implied FX rate between two currencies using a benchmark basket.

    benchmark_pairs yields tuples:
      (price_in_base, price_in_quote, weight)

    implied rate is median(price_quote / price_base), weighted.
    """
    values: list[tuple[Decimal, float]] = []
    n = 0
    for p_base, p_quote, w in benchmark_pairs:
        if p_base <= 0 or p_quote <= 0 or w <= 0:
            continue
        values.append((p_quote / p_base, float(w)))
        n += 1
    if n == 0:
        raise ValueError("No valid benchmark pairs provided")

    rate = weighted_median(values)
    return ImpliedFXResult(base_ccy=base_ccy, quote_ccy=quote_ccy, implied_rate=rate, n=n)
