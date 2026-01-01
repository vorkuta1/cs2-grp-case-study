# Venue & Rail Modeling

To accurately price cross-border arbitrage, we model the specific frictions of every **Venue** and **Settlement Rail**. 

A `VenueModel` encapsulates more than just fees; it models the entire lifecycle of a trade from "Buy" to "Cash in Bank".

## The Venue Model

Defined in `src/cs2_arb/venue.py`:

```python
@dataclass
class VenueModel:
    name: str
    currency: str          # e.g. "USD", "EUR", "CNY", "USD_steam"
    buy_fee: FeeStructure  # Buyer-paid fees
    sell_fee: FeeStructure # Seller-paid fees
    settlement_days: int   # Lockup duration
    risk_score: float      # Counterparty risk
```

### Fee Structure
Fees can be fixed, percentage-based, or asymmetric (Buyer pays vs Seller pays).
- **Buy Cost**: $Price \times (1 + Fee_{buy}) + Fixed_{buy}$
- **Sell Proceeds**: $Price \times (1 - Fee_{sell}) - Fixed_{sell}$

This distinction is critical. On some marketplaces, the buyer pays a service fee (increasing cost basis), while on others the seller pays the commission (reducing netback).

## Settlement Rails & Currency
We distinguish between **Cash** and ** Restricted** currencies.

- **USD (Cash)**: Bank-transferable United States Dollar.
- **USD (Steam)**: Wallet balance, not directly withdrawable.
- **CNY (Buff)**: Often requires specific rails (Alipay/Bank) with withdrawal limits.

### Rail Friction
When moving money between venues, valid routes often involve conversion friction even if the "currency code" is the same.
- **Rail Friction**: Modeled in `normalization.py`. E.g., withdrawing from a "Cash" venue to a Bank Account might incur a 1% fee.
- **Cross-Currency**: Incurs both FX Rate volatility and Rail Friction.

## Risk Scoring
Every venue has a `risk_score` (0.0 - 1.0).
- **0.05**: Established, regulated exchange.
- **0.1-0.2**: Grey-market P2P venue.
- **0.5+**: High-risk new venue or sanction-risk flag.

The final **Route Score** discounts the expected edge by this risk factor: $Edge_{adj} = Edge \times (1 - RiskScore)$.
