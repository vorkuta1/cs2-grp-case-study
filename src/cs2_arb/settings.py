from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CS2ARB_", env_file=".env")

    base_ccy: str = "USD"
    cache_path: str = "data/cache.db"

    ecb_daily_url: str = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"

    # Sell-side fee assumptions (override via env vars)
    fee_steam_pct: float = 0.15
    fee_buff_pct: float = 0.02
