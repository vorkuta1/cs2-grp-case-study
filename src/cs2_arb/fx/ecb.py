from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal

import httpx

from cs2_arb.storage.sqlite_cache import SqliteCache


class ECBRates:
    """
    Fetches ECB EUR reference rates (EUR base) and stores in local cache.

    Feed: https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
    """

    def __init__(self, cache: SqliteCache, url: str):
        self.cache = cache
        self.url = url

    def update(self) -> tuple[date, dict[str, Decimal]]:
        xml = httpx.get(self.url, timeout=20.0).text
        rates_date, rates = self._parse(xml)
        self.cache.put_fx_rates(
            "ECB", rates_date.isoformat(), {k: str(v) for k, v in rates.items()}
        )
        return rates_date, rates

    def latest(self) -> tuple[date, dict[str, Decimal]]:
        hit = self.cache.get_latest_fx_rates("ECB")
        if hit is not None:
            d, rates = hit
            return date.fromisoformat(d), {k: Decimal(v) for k, v in rates.items()}
        return self.update()

    @staticmethod
    def _parse(xml: str) -> tuple[date, dict[str, Decimal]]:
        root = ET.fromstring(xml)
        cubes = [el for el in root.iter() if el.tag.endswith("Cube")]
        time_el = next((c for c in cubes if "time" in c.attrib), None)
        if time_el is None:
            raise ValueError("ECB XML parse error: missing time attribute")
        d = date.fromisoformat(time_el.attrib["time"])
        rates: dict[str, Decimal] = {"EUR": Decimal("1")}
        for c in list(time_el):
            if "currency" in c.attrib and "rate" in c.attrib:
                rates[c.attrib["currency"]] = Decimal(c.attrib["rate"])
        return d, rates


def convert(amount: Decimal, from_ccy: str, to_ccy: str, ecb_rates: dict[str, Decimal]) -> Decimal:
    """
    Convert via EUR base rates:
      X->Y is (amount / rate[X]) * rate[Y]
    """
    f = from_ccy.upper()
    t = to_ccy.upper()
    if f == t:
        return amount
    if f not in ecb_rates or t not in ecb_rates:
        raise KeyError(f"Missing FX rate for {f} or {t}")

    eur = amount if f == "EUR" else (amount / ecb_rates[f])
    return eur if t == "EUR" else (eur * ecb_rates[t])
