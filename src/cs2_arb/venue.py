from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class FeeStructure:
    pct: float
    fixed: Decimal = Decimal("0")
    
    def calculate_cost(self, amount: Decimal) -> Decimal:
        """Calculates total cost added to a base amount (amount + fees)."""
        pct = Decimal(str(self.pct))
        return amount * (Decimal("1") + pct) + self.fixed

    def calculate_proceeds(self, amount: Decimal) -> Decimal:
        """Calculates net proceeds from a base amount (amount - fees)."""
        pct = Decimal(str(self.pct))
        return (amount * (Decimal("1") - pct)) - self.fixed


@dataclass
class VenueModel:
    name: str
    currency: str  # e.g., "USD_cash", "USD_steam_wallet"
    
    # Fees
    buy_fee: FeeStructure
    sell_fee: FeeStructure
    
    # Settlement constraints
    settlement_days: int = 0  # Lockup / Withdrawal delay
    
    # Risk
    risk_score: float = 0.0  # 0.0 (safe) to 1.0 (scam)
    
    # Supported Rails (e.g. "bank", "crypto")
    rail_options: list[str] = field(default_factory=list)

    @property
    def is_cash(self) -> bool:
        return "cash" in self.currency.lower()
