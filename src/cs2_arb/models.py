from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

# We import FeeStructure as MarketFee for backward compatibility if needed,
# or we just rely on VenueModel having it.
# For now, we leave the old MarketFee here if it's used elsewhere, but marked for deprecation?
# Actually, let's keep it simple. If we want clean code, let's align.
# But I won't delete MarketFee yet to avoid massive breakage in one go.


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


@dataclass
class Route:
    listing_id: str
    item_key: str
    buy_venue: str
    sell_venue: str
    
    # Prices in USD (or Numeraire)
    buy_cost_usd: Decimal
    sell_proceeds_usd: Decimal
    
    # Metrics
    edge_raw: float  # (proceeds - cost) / cost
    roi_pct: float   # edge_raw * 100
    
    # Haircuts (0.0 = no penalty, 1.0 = full penalty / worthless)
    liquidity_haircut: float
    lockup_haircut: float
    risk_haircut: float
    
    # Final Score
    score: float

    def summary(self) -> str:
        return (
            f"{self.buy_venue}->{self.sell_venue} | "
            f"Buy: ${self.buy_cost_usd:.2f} | Sell: ${self.sell_proceeds_usd:.2f} | "
            f"Edge: {self.roi_pct:.1f}% | Score: {self.score:.2f}"
        )


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
    # DEPRECATED: Use VenueModel.FeeStructure
    pct: float
    fixed: Decimal = Decimal("0")


class GRPPoint(BaseModel):
    item_key: str
    ts: datetime
    grp_usd: Decimal
    n_sources: int = Field(ge=1)
