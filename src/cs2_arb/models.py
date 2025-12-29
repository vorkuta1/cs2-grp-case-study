from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PricePrint(BaseModel):
    market: str
    item_key: str
    currency: str
    price: Decimal
    ts: datetime

    volume_7d: float | None = None
    spread: float | None = None  # fraction, e.g. 0.02 = 2%


class Listing(BaseModel):
    listing_id: str
    item_key: str
    market: str
    currency: str
    ask: Decimal
    ts: datetime

    # Metadata
    rarity: str = (
        "Common"  # Consumer Grade, Industrial, Mil-Spec, Restricted, Classified, Covert, Contraband
    )

    age_seconds: int | None = None

    # Feature attributes
    float_value: float | None = None
    min_cap: float | None = None
    max_cap: float | None = None
    seed: int | None = None  # pattern seed
    stickers: str | None = None  # JSON string or structured list representation


class ListingFeatures(BaseModel):
    """Encapsulates the specific features of an item instance."""

    float_value: float | None = None
    min_cap: float | None = None
    max_cap: float | None = None
    seed: int | None = None
    stickers: list[dict] | None = None  # List of {id, slot, wear}
    rarity: str = "Common"


@dataclass(frozen=True)
class MarketFee:
    # Simple sell-side fee model (pct + fixed).
    pct: float
    fixed: Decimal = Decimal("0")


class GRPPoint(BaseModel):
    item_key: str
    ts: datetime
    grp_usd: Decimal
    n_sources: int = Field(ge=1)
