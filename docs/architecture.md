# Architecture

This repo is intentionally written as a **platform-engineering** case study: 
a small, testable pricing engine with clear module boundaries (markets / FX / pricing / scoring / storage).

## Data-flow (batch)

```mermaid
flowchart LR
  A("Market adapters<br/>(Steam, Buff, ...)") -->|price prints & listings| B("Normalizer<br/>(Fees, FX, Haircuts)")
  B --> C("GRP Engine<br/>(Weighted Median)")
  C --> D("Feature models<br/>(Float, Pattern, Sticker)")
  D --> E("Opportunity Scorer<br/>(Edge x Liquidity)")
  E --> F("Outputs<br/>(Console / DB)")
```

## Currency layer

Two distinct FX concepts are modeled:

- **Official FX**: central-bank FX (ECB daily reference rates), used as the first-pass normalization.
- **Implied / Effective FX**: a *market-specific* FX inferred from cross-listed benchmark items. This captures
  persistent basis caused by settlement constraints, regional demand, and platform frictions.

```mermaid
flowchart TB
  ECB[ECB EUR refs] --> FX1[Official FX table]
  Bench("Benchmark basket<br/>(High-Liq Items)") --> IFX("Implied FX est.")
  FX1 --> Norm("Currency Normalization")
  IFX --> Norm
  Norm --> GRP[Global Reference Price]
```