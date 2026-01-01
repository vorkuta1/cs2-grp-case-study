from decimal import Decimal

from cs2_arb.pricing.curves import FloatCurveParams, float_multiplier
from cs2_arb.pricing.features import FeatureConfig, pattern_multiplier


def test_float_multiplier_phases() -> None:
    params = FloatCurveParams(
        has_high_float_premium=True, f1_cutoff=Decimal("0.02"), f2_cutoff=Decimal("0.45")
    )

    # Phase I: Low float (0.001) should have high multiplier
    # e^(-150 * 0.001) = e^(-0.15) ≈ 0.86
    # 1 + 2.5 * 0.86 ≈ 3.15
    f_low = Decimal("0.001")
    m_low = float_multiplier(f_low, params)
    assert m_low > Decimal("2.0")

    # Phase II: Normal float (0.20) should be 1.0
    f_mid = Decimal("0.20")
    m_mid = float_multiplier(f_mid, params)
    assert m_mid == Decimal("1.0")

    # Phase III: High float (0.90) should have premium
    # 0.90 > 0.45 cutoff
    f_high = Decimal("0.90")
    m_high = float_multiplier(f_high, params)
    assert m_high > Decimal("1.0")


def test_pattern_multiplier() -> None:
    cfg = FeatureConfig(pattern_multipliers={661: Decimal("5.0"), 387: Decimal("10.0")})

    # Tier 1 seed
    assert pattern_multiplier(661, cfg) == Decimal("5.0")

    # Random seed
    assert pattern_multiplier(123, cfg) == Decimal("1.0")

    # None seed
    assert pattern_multiplier(None, cfg) == Decimal("1.0")
