from __future__ import annotations

from abc import ABC, abstractmethod

from cs2_arb.models import Listing, PricePrint


class MarketAdapter(ABC):
    name: str

    @abstractmethod
    def load_price_prints(self, path: str) -> list[PricePrint]:
        raise NotImplementedError

    @abstractmethod
    def load_listings(self, path: str) -> list[Listing]:
        raise NotImplementedError
