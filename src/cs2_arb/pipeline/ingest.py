from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from cs2_arb.models import Listing, PricePrint


def group_prints_by_item(prints: Iterable[PricePrint]) -> dict[str, list[PricePrint]]:
    out: dict[str, list[PricePrint]] = defaultdict(list)
    for p in prints:
        out[p.item_key].append(p)
    return dict(out)


def group_listings_by_item(listings: Iterable[Listing]) -> dict[str, list[Listing]]:
    out: dict[str, list[Listing]] = defaultdict(list)
    for listing in listings:
        out[listing.item_key].append(listing)
    return dict(out)
