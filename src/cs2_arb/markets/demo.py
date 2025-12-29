from __future__ import annotations

import json

from cs2_arb.markets.base import MarketAdapter
from cs2_arb.models import Listing, PricePrint


class DemoJSONMarket(MarketAdapter):
    name = "demo"

    def load_price_prints(self, path: str) -> list[PricePrint]:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return [PricePrint.model_validate(x) for x in data]

    def load_listings(self, path: str) -> list[Listing]:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return [Listing.model_validate(x) for x in data]
