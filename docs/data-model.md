# Data model

This engine uses two primary record types:

## PricePrint

A _trade print_ or _best-available quote_ (depending on what the source provides).

Fields:

- `market`: e.g. `steam`, `buff163`
- `item_key`: canonical identifier (weapon + finish + special flags + wear bucket + seed class)
- `currency`: ISO 4217 (e.g., `USD`, `EUR`, `CNY`)
- `price`: decimal as string
- `ts`: ISO timestamp
- `volume_7d`: optional
- `spread`: optional (if available)

## Listing

An individual listing we might buy (ask) or sell (bid).

Fields:

- `market`, `listing_id`, `item_key`, `currency`, `ask`, `ts`
- optional microstructure fields: `age_seconds`, `seller_reputation`, etc.

### Canonical item_key

This repo uses a simple canonical key:

`<weapon>|<finish>|<flags>|<wear_bucket>|<seed_tier>`

Example:
`AK-47|Redline|stattrak=false,souvenir=false|FT|seed=any`

Real production systems will normalize across these dimensions. The `Listing` model now supports:

- **Float**: High-precision float value (e.g., `0.0000123`).
- **Caps**: Min/Max float caps for the item.
- **Pattern Seed**: Integer seed for pattern-based skins (Case Hardened, Doppler).
- **Stickers**: List of applied stickers with slot and wear info.

## VenueModel

Encapsulates the friction and risk profile of a marketplace.

Fields:
- `name`: unique identifier
- `currency`: base settlement currency (e.g. `USD_steam_wallet`)
- `buy_fee`: `(pct, fixed)` structure for buyer-paid fees
- `sell_fee`: `(pct, fixed)` structure for seller-paid fees
- `settlement_days`: lockup period
- `risk_score`: 0.0-1.0 probability of failure/scam
- `rail_options`: supported withdrawal rails

## Route

A scored arbitrage path from Buy Venue A to Sell Venue B.

Fields:
- `buy_venue`, `sell_venue`: names
- `buy_cost_usd`: total normalized cost
- `sell_proceeds_usd`: total normalized net proceeds
- `edge_raw`: simple ROI percentage
- `score`: final risk-adjusted quality score
- `liquidity_haircut`: penalty for time-to-sell
- `lockup_haircut`: penalty for capital cost
- `risk_haircut`: penalty for venue trust

## Feature Logic

The `ListingFeatures` class encapsulates these attributes to drive the **Feature Model**, which adjusts the Global Reference Price (GRP) to a specific **Model Price** for the item instance. See [`docs/quant-model.md`](quant-model.md) for the mathematical details.
