# Architecture

This repo is intentionally written as a **platform-engineering** case study: 
a small, testable pricing engine with clear module boundaries (markets / FX / pricing / scoring / storage).

## Data-flow (batch)

```mermaid
flowchart LR
  A["Market adapters<br/>Steam / Buff / ..."] -->|price prints & listings| B["Normalizer<br/>fees + FX + settlement haircuts"]
  B --> C["GRP Engine<br/>weighted median"]
  C --> D["Feature models<br/>float/pattern/sticker"]
  D --> E["Opportunity Scorer<br/>edge x liquidity"]
  E --> F["Outputs<br/>console / parquet / sqlite"]
```

## Currency layer

Two distinct FX concepts are modeled:

- **Official FX**: central-bank FX (ECB daily reference rates), used as the first-pass normalization.
- **Implied / Effective FX**: a *market-specific* FX inferred from cross-listed benchmark items. This captures
  persistent basis caused by settlement constraints, regional demand, and platform frictions.

```mermaid
flowchart TB
  ECB["ECB EUR reference rates"] --> FX1["Official FX table"]
  Bench["Benchmark basket<br/>high-liquidity items"] --> IFX["Implied FX estimator"]
  FX1 --> Norm["Currency normalization"]
  IFX --> Norm
  Norm --> GRP["Global Reference Price"]
```