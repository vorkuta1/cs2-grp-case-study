# Usage Guide

This repository includes a CLI tool `cs2arb` (or `python -m cs2_arb.cli`) to interact with the pricing engine.

## Installation

Ensure you have a recent Python environment (3.11+).

```bash
uv sync  # or install dependencies manually
```

## Commands

### 1. Feature Scoring (`features score-listing`)

Compute the feature-adjusted **Model Price** for a hypothetical item.

```bash
uv run cs2arb features score-listing --base-price 100.0 --float-val 0.001
```

Options:
- `--base-price`: The GRP (Global Reference Price) for the generic item.
- `--float-val`: The specific float of the listing.
- `--seed`: Pattern seed (optional).
- `--stickers-json`: JSON string representing stickers, e.g. `[{"id": 123, "slot": 0, "wear": 0}]`.

### 2. Manufacturing Analysis (`manufacturing analyze`)

Analyze the profitability of a trade-up contract or "crafting" operation.

```bash
uv run cs2arb manufacturing analyze \
  --input-prices "10.50, 10.50, 11.00, 10.75" \
  --output-prices "50.00, 60.00, 12.00" \
  --rarity "Mil-Spec" \
  --ops-cost 0.50
```

To analyze a **Covert -> Knife** contract (which uses 5 inputs):

```bash
uv run cs2arb manufacturing analyze \
  --input-prices "100.0, 100.0, 100.0, 100.0, 100.0" \
  --output-prices "800.0, 400.0" \
  --rarity "Covert"
```

Calculates Input Cost, Output EV, and theoretical Edge.

### 3. End-to-End Demo (`demo run`)

Run the full pipeline on fixture data. This ingests listings and price prints (from `data/`), computes GRP, applies feature multipliers (if data exists), and ranks top opportunities.

```bash
uv run cs2arb demo run --prices data/demo_prices.json --listings data/demo_listings.json
```

## Examples

### Low Float Premier
A "Triple Zero" float (0.000x) significantly boosts the model price via the Phase I feature curve.

```bash
uv run cs2arb features score-listing --base-price 100 --float-val 0.0005
# Returns > 1.0x multiplier
```

### High Float Anomaly
Some skins have a "Black Scope" or similar high-float feature (Phase III).

```bash
uv run cs2arb features score-listing --base-price 50 --float-val 0.99
# Returns > 1.0x multiplier if high-float premium is enabled in config
```
