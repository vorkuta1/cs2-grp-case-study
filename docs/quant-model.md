# Quantitative Model & Methodology

This document details the mathematical framework used for the pricing and scoring engine.

## 1. Standardization & Currency Layer

### 1.1 Net-of-fees Proceeds
To make prices comparable across venues, we compute the realizable net floating cash for seller `m` listing item `i`:

$$
p^{net}_{m}(i,t)=FX^{eff}_{c_m\to USD}(t)\cdot\Big(p^{raw}_{m}(i,t)\cdot(1-fee^{sell}_{m})-fee^{fixed}_{m}\Big)
$$

### 1.2 Effective FX
We model the realizable exchange rate, accounting for conversion friction and rail choice:

$$
FX^{eff} = FX^{spot}\cdot (1-\eta_{conv}-\eta_{wd}-\eta_{spread})
$$

This allows modeling "Steam USD" separate from "Cash USD".

### 1.3 Currency Basis
We interpret persistent deviations in cross-venue arbitrage intervals as an implied currency basis (CNY vs USD):

$$
Basis_{FX}(t)=\text{wMedian}\left(\frac{p^{net}_{CN}}{p^{net}_{US}}\right) - 1
$$

## 2. Global Reference Price (GRP)

We aggregate normalized prints from all venues to form a single consensus price.

### 2.1 Confidence Weighting

$$
w_m(i,t)=\sqrt{Vol_m}\cdot e^{-\Delta t/\tau}\cdot\frac{1}{Spread_m+\epsilon}\cdot q_m
$$

*   `q_m`: Venue quality score (0.0-1.0).

### 2.2 Aggregation

$$
P^{GRP}(i,t)=\text{wMedian}\big(\{p^{net}_{m}\},\{w_m\}\big)
$$

Weighted median is preferred over mean to reject outliers without explicit filtering thresholds.

## 3. Feature Pricing Model

A "Base Item" price (GRP) is adjusted for specific feature attributes of a unique listing `l`:

$$
P^{model}(l) = P^{GRP} \cdot M_{float}(f) \cdot M_{pattern}(s) \cdot M_{stickers}(S)
$$

### 3.1 Tri-Phase Float Curve ($M_{float}$)
1.  **Phase I (Perfection)**: Exponential premium for $f \to 0$.
    $M(f) = 1 + \alpha e^{-\beta f}$
2.  **Phase II (Wear Buckets)**: Standard market pricing (flat 1.0 multiplier on bucket-specific GRP).
3.  **Phase III (High-Float)**: Scarcity premium for maximum wear caps.
    $M(f) = 1 + \gamma e^{\delta(f-f_2)}$

### 3.2 Pattern Tiers ($M_{pattern}$)
Algorithmic lookup based on seed `k`:

$$
M_{pattern}(k) = \begin{cases} \mu_{Tier1} & \text{if } k \in \text{BlueGem} \\ 1.0 & \text{otherwise} \end{cases}
$$

### 3.3 Sticker Valuation ($M_{stickers}$)
Modeled as a "scrap value" plus a "synergy premium":

$$
M_{stickers} = 1 + \rho \sum \frac{p_{sticker}}{P_{base}} + \lambda \sigma(S) \frac{\sum p_{sticker}}{P_{base}}
$$

*   $\sigma(S)$: Synergy score (e.g., 4x same sticker = 1.0, random = 0.0).

## 4. Manufacturing Anchor (Crafting)

For items that can be created via Trade Up Contracts:

-   **Input Cost**: Cost to acquire 10 (or 5) inputs.
    $Cost_{in} = N_{in} \cdot P^{GRP}(InputClass) + OpsCost$
-   **Output EV**: Expected value of outcomes.
    $EV_{out} = \sum P(outcome_i) \cdot P^{GRP}(outcome_i)$
-   **Manufacturing Edge**:
    $Edge = EV_{out} - Cost_{in}$

This effectively sets a "floor" price for inputs and a "ceiling" for outputs (arbitrageable if violated).

## 5. Opportunity Scoring

Rank listings by risk-adjusted profitability.

### 5.1 Raw Edge

$$
Edge = \frac{P^{model}_{net} - Ask_{net}}{Ask_{net}}
$$

### 5.2 Haircuts
Discount the edge by liquidity (time-to-sell) and capital lockup costs:

$$
H_{liq} = e^{-TTS / \tau_{sell}}
$$
$$
H_{lock} = e^{-LockDays \cdot r_{risk\_free}}
$$
$$
H_{risk} = 1 - P(failure)
$$

### 5.3 Final Score

$$
Score = Edge \cdot H_{liq} \cdot H_{lock} \cdot H_{risk}
$$
