from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
from core.utils.money import qround, EPS

class SplitStrategy(ABC):
    @abstractmethod
    def split(self, amount: float, participants: Dict[str, float | int]) -> Dict[str, float]:
        ...

class EqualSplit(SplitStrategy):
    def split(self, amount: float, participants: Dict[str, float | int]) -> Dict[str, float]:
        users = list(participants.keys())
        n = len(users)
        base = amount / n
        # Initial rounded shares
        shares = [qround(base) for _ in users]
        # Distribute remainder cents fairly by largest fractional part
        diff = qround(amount - sum(shares))
        # If rounding caused a shortfall/excess, adjust a cent at a time
        i = 0
        step = 0.01 if diff > 0 else -0.01
        while abs(diff) >= 0.01 - EPS and i < 1000:
            idx = i % n
            shares[idx] = qround(shares[idx] + step)
            diff = qround(amount - sum(shares))
            i += 1
        return {u: s for u, s in zip(users, shares)}

class ExactSplit(SplitStrategy):
    def split(self, amount: float, participants: Dict[str, float | int]) -> Dict[str, float]:
        total = float(sum(float(v) for v in participants.values()))
        if abs(total - amount) > 0.01 + EPS:  # allow 1 cent float wiggle
            raise ValueError(f"Exact split totals {total:.2f}, not {amount:.2f}")
        return {name: qround(float(v)) for name, v in participants.items()}

class ShareSplit(SplitStrategy):
    def split(self, amount: float, participants: Dict[str, float | int]) -> Dict[str, float]:
        weights = {k: float(v) for k, v in participants.items()}
        if any(w <= 0 for w in weights.values()):
            raise ValueError("All shares must be positive.")
        total_w = sum(weights.values())
        raw = {k: (amount * (w / total_w)) for k, w in weights.items()}
        # Round & fix remainder like Equal
        users = list(raw.keys())
        shares = [qround(raw[u]) for u in users]
        diff = qround(amount - sum(shares))
        i = 0
        step = 0.01 if diff > 0 else -0.01
        while abs(diff) >= 0.01 - EPS and i < 1000:
            idx = i % len(users)
            shares[idx] = qround(shares[idx] + step)
            diff = qround(amount - sum(shares))
            i += 1
        return {u: s for u, s in zip(users, shares)}
