# Data model

This engine uses two primary record types:

## PricePrint

A *trade print* or *best-available quote* (depending on what the source provides).

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

## Feature Logic

The `ListingFeatures` class encapsulates these attributes to drive the **Feature Model**, which adjusts the Global Reference Price (GRP) to a specific **Model Price** for the item instance. See [`docs/quant-model.md`](quant-model.md) for the mathematical details.
