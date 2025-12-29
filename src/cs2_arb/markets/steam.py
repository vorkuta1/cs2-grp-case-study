from __future__ import annotations

import json

from cs2_arb.markets.base import MarketAdapter
from cs2_arb.models import Listing, MarketFee, PricePrint


class SteamMarketAdapter(MarketAdapter):
    name = "steam"

    def __init__(self, fees: dict[str, MarketFee]) -> None:
        self.fees = fees

    def load_price_prints(self, path: str) -> list[PricePrint]:
        """Simulate loading price prints from a local JSON file."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        return [PricePrint.model_validate(x) for x in data]

    def load_listings(self, path: str) -> list[Listing]:
        """Simulate loading listings from a local JSON file."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        return [Listing.model_validate(x) for x in data]
