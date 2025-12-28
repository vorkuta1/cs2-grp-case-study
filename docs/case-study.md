# Case study: Multi-venue price normalization for an illiquid digital market (CS2)

## Why this exists

As a systems/platform engineer targeting remote roles in **commodities / physical trade**, I wanted a public case study that demonstrates the same engineering + market structure problems you see in real-world flows:

- **Multi-venue price discovery** (different marketplaces, different rules)
- **FX normalization + basis** (official vs effective FX)
- **Fees, settlement constraints, and carry** (like freight, storage, and credit terms)
- **Manufacturing / transformation economics** (Covert → Gold trade-up resembles input→output spreads)

The domain here is Counter-Strike 2 skins, but the *engineering* and *market microstructure* are the point.

## The shock that motivated the design

Valve’s October 2025 update expanded Trade Up Contracts so **5 Covert items can be exchanged for a Knife/Gloves** from the corresponding collection. This created a sudden “manufacturing” pathway for gold-tier items and reshaped supply dynamics. (The patch note is the primary source.)

## The core deliverable

A **Global Reference Price (GRP)** that is:
- cross-market comparable
- net-of-fees
- currency-normalized (USD base)
- robust to outliers (weighted median)
- liquidity-weighted and time-decayed

And an **Opportunity Score** that turns thousands of listings into a ranked queue.

## Currency: the missing dimension

This market is international. Steam sells and settles in local wallet currencies and applies its own FX conversion when buyer/seller wallets differ (updated daily). 
Steam wallet funds are not withdrawable to a bank account, which makes “Steam USD” behave like a restricted settlement currency rather than cash. 

Meanwhile, Chinese marketplaces (commonly BUFF.163 / BUFF Market) are CNY-settled and often act like a liquidity center for certain items, creating repeated cross-venue basis events that look like classic
geographic arbitrage.

This repo models currency in two layers:

1. **Official FX (ECB daily reference rates)** used as the default normalization. 
2. **Implied (effective) FX** inferred from a basket of cross-listed “benchmark” items, capturing persistent basis.

## What is *not* included

- No scraping bypasses. Market adapters are written to accept **exported data** (JSON/CSV) or official APIs.
- No account automation, no trade bots, no instructions to bypass platform controls.

## How to read the repo

- `src/cs2_arb/fx/`:
  - `ecb.py`: pulls and caches ECB EUR reference rates
  - `implied.py`: infers effective FX via benchmark basket
- `src/cs2_arb/pricing/grp.py`: weighted-median GRP engine
- `src/cs2_arb/pricing/features.py`: float/pattern/sticker multipliers
- `src/cs2_arb/pricing/manufacturing.py`: input basket vs output EV
- `src/cs2_arb/scoring/opportunity.py`: edge + liquidity haircuts
- `src/cs2_arb/markets/demo.py`: demo adapter reading local JSON fixtures
