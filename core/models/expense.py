# Forward references for type hints; keeps compatibility across Python versions
from __future__ import annotations

# dataclasses: reduce boilerplate for “data holder” classes
from dataclasses import dataclass, field

# datetime: we timestamp expenses/settlements and serialize them
from datetime import datetime

# typing: Dict for mappings, Optional for nullable group_id
from typing import Dict, Optional

# SplitStrategy defines how we divide amounts (Equal/Exact/Share)
from .splits import SplitStrategy


@dataclass
class Expense:
    """Represents a single shared expense and its split configuration."""
    id: str
    description: str
    amount: float
    payer: str
    participants: Dict[str, float | int]      # strategy-dependent payload
    split_strategy: SplitStrategy              # Equal/Exact/Share object
    notes: str = ""
    date: datetime = field(default_factory=datetime.utcnow)
    group_id: Optional[str] = None

    def allocations(self) -> Dict[str, float]:
        """Return per-participant owed amounts per the chosen strategy."""
        return self.split_strategy.split(self.amount, self.participants)


@dataclass
class Settlement:
    """Represents a payment from payer → payee that reduces debt."""
    id: str
    payer: str           # who pays now (e.g., you)
    payee: str           # who receives
    amount: float
    description: str = ""
    date: datetime = field(default_factory=datetime.utcnow)
    notes: str = ""
