from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class FloatCurveParams:
    # Phase I
    alpha: Decimal = Decimal("2.5")
    beta: Decimal = Decimal("150")
    f1_cutoff: Decimal = Decimal("0.02")  # End of Phase I

    # Phase III
    gamma: Decimal = Decimal("0.5")
    delta: Decimal = Decimal("10.0")
    f2_cutoff: Decimal = Decimal("0.45")  # Start of Phase III (high float)

    has_high_float_premium: bool = False


def normalize_float(f: Decimal, min_cap: Decimal, max_cap: Decimal) -> Decimal:
    """Unroll float f onto [0, 1] range given caps."""
    if max_cap <= min_cap:
        return Decimal("0")  # fallback
    return (f - min_cap) / (max_cap - min_cap)


def float_multiplier(f: Decimal, params: FloatCurveParams | None = None) -> Decimal:
    """
    Compute float multiplier based on Tri-Phase curve.
    Uses raw float value f to determine phase (I vs III).
    """
    import math

    params = params or FloatCurveParams()

    # Phase I: Perfection Tail
    if f <= params.f1_cutoff:
        return Decimal("1") + params.alpha * Decimal(str(math.exp(-float(params.beta) * float(f))))

    # Phase III: High Float Anomalies
    if params.has_high_float_premium and f > params.f2_cutoff:
        # M = 1 + gamma * e^(delta * (f - f2))
        return Decimal("1") + params.gamma * Decimal(
            str(math.exp(float(params.delta) * (float(f) - float(params.f2_cutoff))))
        )

    # Phase II: Wear Buckets
    return Decimal("1")
