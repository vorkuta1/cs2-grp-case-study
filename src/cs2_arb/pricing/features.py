from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from cs2_arb.models import ListingFeatures
from cs2_arb.pricing.curves import FloatCurveParams, float_multiplier


@dataclass(frozen=True)
class FeatureConfig:
    float_params: FloatCurveParams = FloatCurveParams()
    # Pattern tiers: seed -> tier multiplier
    pattern_multipliers: dict[int, Decimal] | None = None
    # Sticker params
    sticker_scrap_value_ratio: Decimal = Decimal("0.05")  # rho
    sticker_synergy_factor: Decimal = Decimal("0.1")  # lambda


def pattern_multiplier(seed: int | None, cfg: FeatureConfig) -> Decimal:
    if seed is None or not cfg.pattern_multipliers:
        return Decimal("1.0")
    return cfg.pattern_multipliers.get(seed, Decimal("1.0"))


def sticker_multiplier(
    stickers: list[dict] | None,
    base_price: Decimal,
    cfg: FeatureConfig,
    sticker_prices: dict[int, Decimal] | None = None,
) -> Decimal:
    """
    Compute sticker multiplier based on the formula:
    M_stickers(S) = 1 + lambda * sigma(S) * (sum(p_sticker) / B_sw)

    where:
    - lambda: synergy factor config
    - sigma(S): consistency/synergy score (e.g., all same sticker)
    - p_sticker: individual price of applied stickers
    - B_sw: base price of the skin
    """
    if not stickers or base_price <= 0:
        return Decimal("1.0")

    total_sticker_price = Decimal("0")
    for s in stickers:
        price = Decimal("0")
        s_id = s.get("id")
        if sticker_prices and s_id is not None and s_id in sticker_prices:
            price = sticker_prices[s_id]
        else:
            # Fallback to embedded price if present (legacy)
            price = Decimal(str(s.get("price", 0)))
        total_sticker_price += price

    if total_sticker_price == 0:
        return Decimal("1.0")

    # Consistency/Synergy score (sigma).
    # 1.0 if 4x same sticker, 0.5 otherwise.
    sigma = Decimal("0.5")
    if len(stickers) >= 4:
        # Check if all same id
        first_id = stickers[0].get("id")
        if all(s.get("id") == first_id for s in stickers):
            sigma = Decimal("1.0")

    ratio = total_sticker_price / base_price
    return Decimal("1.0") + cfg.sticker_synergy_factor * sigma * ratio


def compute_model_price(
    base_grp: Decimal,
    features: ListingFeatures,
    cfg: FeatureConfig,
    sticker_prices: dict[int, Decimal] | None = None,
) -> Decimal:
    """
    P_model = B * M_float * M_pattern * M_stickers
    """
    # 1. Float
    f = Decimal(str(features.float_value)) if features.float_value is not None else Decimal("0")
    m_float = float_multiplier(f, cfg.float_params)

    # 2. Pattern
    m_pattern = pattern_multiplier(features.seed, cfg)

    # 3. Stickers
    # stickers list of dicts.
    m_sticker = sticker_multiplier(features.stickers, base_grp, cfg, sticker_prices)

    return base_grp * m_float * m_pattern * m_sticker
