# CS2 GRP Case Study

A case study for **multi-venue, multi-currency price normalization** and opportunity ranking in an illiquid market.

The domain is CS2 skins; the value is the **market understanding + data engineering**:
FX normalization, fees, robust aggregation, caching, and a clean module boundary design.

**New in v0.2**:
- **Feature Model**: Tri-phase float curves, pattern tiers, and sticker valuations.
- **Manufacturing Anchor**: Input-basket economics for trade-up contracts ("crafting").
- **Simulated Markets**: File-based adapters for Steam/Buff to enable consistent testing.

## Why it’s relevant to commodities / physical trade

If you strip the paint off the skins:

- marketplaces = exchanges / brokers
- Steam Wallet = restricted settlement currency (Steam USD $\neq$ Cash USD)
- fees = transaction costs
- trade holds = inventory carry / settlement delay
- Covert $\to$ Gold = input $\to$ output manufacturing spread
- regional basis (West vs China) = geographic arbitrage / basis trading

This repo demonstrates the same system design decisions: **normalize, de-bias, score, and rank**.

## What it does

1. Ingest price prints and listings from multiple venues.
2. Normalize:
   - net-of-fees
   - currency to USD (ECB FX by default)
   - optional implied FX basis per venue (treating restricted usage currencies like Steam Wallet separately)
3. Compute a **Global Reference Price (GRP)** via weighted median:
   $P^{GRP} = \text{wMedian}(\{P_{net}\}, \{Weights\})$
4. Apply **Feature Multipliers** to compute a **Model Price**:
   $P^{model} = P^{GRP} \cdot M_{float} \cdot M_{pattern} \cdot M_{stickers}$
   - *Float*: Tri-phase curve (Perfection, Wear Buckets, High-Float).
   - *Pattern*: Tier-based multipliers (e.g., Blue Gem).
   - *Stickers*: Scrap value + Synergy premium.
5. Score listings with an **Opportunity Score**:
   $Score = Edge \cdot H_{liquidity} \cdot H_{lock} \cdot H_{risk}$
   - *Edge*: Model Price vs Net Ask.
   - *Haircuts*: Time-to-sell, inventory lockup, and venue risk.

> Full mathematical details in [`docs/quant-model.md`](docs/quant-model.md).

## Quickstart

### 1) Install

This project uses `uv` for dependency management.

```bash
uv sync
```

### 2) Run the demo

```bash
uv run cs2arb demo run --prices data/demo_prices.json --listings data/demo_listings.json
```

### 3) Feature Scoring

Compute the precise model price for an item with specific attributes (e.g., low float):

```bash
uv run cs2arb features score-listing --base-price 100 --float-val 0.001
```

### 4) Manufacturing Analysis

Analyze input/output spreads (e.g., Trade-Up profitability):

```bash
uv run cs2arb manufacturing analyze --input-prices "10,10,10" --output-prices "50,12"
```

## Documentation

- `docs/case-study.md` – context + framing
- `docs/architecture.md` – data-flow diagrams
- `docs/data-model.md` – listings, prints, and feature schemas
- `docs/usage.md` – detailed CLI usage guide

## Repo map

- `src/cs2_arb/` – package
  - `fx/` – ECB FX + implied FX basis estimator
  - `markets/` – adapters (demo, steam, buff163)
  - `pricing/` – GRP, fee normalization, float curves, manufacturing
  - `scoring/` – opportunity score
  - `storage/` – sqlite cache
- `data/` – fixtures (safe, fake-but-plausible numbers)

## Disclaimer

This project is for engineering demonstration and research.
It does not automate trades, does not bypass platform protections, and is not financial advice.
