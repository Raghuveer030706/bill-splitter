# asdict: convert simple dataclasses to dicts for JSON storage
from dataclasses import asdict

# typing: Dict/Any/List/Optional for clean, explicit signatures
from typing import Dict, Any, List, Optional, Tuple

# datetime: parse ISO strings back to datetime
from datetime import datetime

# Local domain models
from core.models.expense import Expense, Settlement
from core.models.ledger import Ledger

# Persistence + auth services
from core.services.cache import CacheService
from core.services.auth import AuthService

# Split strategies: used to re-instantiate strategy objects by name
from core.models.splits import SplitStrategy, EqualSplit, ExactSplit, ShareSplit


class ExpenseManager:
    """
    Orchestrates domain models and persistence for UI consumption.
    - Serializes to CacheService on write
    - Rebuilds Ledger from persisted records on load
    """

    def __init__(self, cache: Optional[CacheService] = None, auth: Optional[AuthService] = None) -> None:
        self.cache = cache or CacheService()
        self.auth = auth or AuthService()
        self.ledger = Ledger()
        self._strategy_map = {
            "EqualSplit": EqualSplit,
            "ExactSplit": ExactSplit,
            "ShareSplit": ShareSplit,
        }
        # Build ledger immediately from whatever is already in cache
        self.rebuild_ledger()

    # ---------- public ops ----------
    def add_expense(self, exp: Expense) -> None:
        """Persist expense → JSON, then rebuild ledger."""
        self.cache.add_expense(self._serialize_expense(exp))
        self.cache.save()
        self.rebuild_ledger()

    def add_settlement(self, st: Settlement) -> None:
        """Persist settlement → JSON, then rebuild ledger."""
        self.cache.add_settlement(self._serialize_settlement(st))
        self.cache.save()
        self.rebuild_ledger()

    def balances_for(self, username: str) -> Dict[str, float]:
        """Convenience for UI: what does `username` owe / is owed by others?"""
        return self.ledger.net_for(username)

    def dashboard_totals(self, username: str) -> Tuple[float, float]:
        """
        Aggregate totals for dashboard cards:
        returns (you_owe_total, others_owe_you_total)
        """
        net = self.ledger.net_for(username)
        you_owe = sum(v for v in net.values() if v > 0)
        others_owe_you = -sum(v for v in net.values() if v < 0)
        return round(you_owe, 2), round(others_owe_you, 2)

    # ---------- reconstruction ----------
    def rebuild_ledger(self) -> None:
        """
        Recompute ledger by deserializing expenses and settlements from cache.
        We apply in chronological order by 'date' to keep mental model consistent.
        """
        self.ledger = Ledger()

        # Build sortable timelines for expenses and settlements
        exps = [self._deserialize_expense(d) for d in self.cache.list_expenses()]
        sets = [self._deserialize_settlement(d) for d in self.cache.list_settlements()]

        # Merge timelines and apply in date order
        timeline: List[Tuple[datetime, str, Any]] = []
        for e in exps:
            timeline.append((e.date, "expense", e))
        for s in sets:
            timeline.append((s.date, "settlement", s))

        timeline.sort(key=lambda t: t[0])  # sort by datetime ascending

        for _, kind, obj in timeline:
            if kind == "expense":
                self.ledger.apply_expense(obj)
            else:
                self.ledger.apply_settlement(obj)

    # ---------- (de)serialization helpers ----------
    def _serialize_expense(self, exp: Expense) -> Dict[str, Any]:
        """
        Make a JSON-friendly dict from an Expense.
        Note: Replace strategy instance with its class name; ISO-encode datetime.
        """
        data = asdict(exp)
        data["split_strategy"] = exp.split_strategy.__class__.__name__
        data["date"] = exp.date.isoformat()
        return data

    def _serialize_settlement(self, st: Settlement) -> Dict[str, Any]:
        """JSON-friendly dict for Settlement with ISO date."""
        data = asdict(st)
        data["date"] = st.date.isoformat()
        return data

    def _deserialize_expense(self, data: Dict[str, Any]) -> Expense:
        """
        Turn dict back into an Expense instance.
        - Re-create strategy object by name
        - Parse ISO date
        """
        strat_name = data["split_strategy"]
        strat_cls = self._strategy_map.get(strat_name)
        if not strat_cls:
            raise ValueError(f"Unknown split strategy: {strat_name}")

        return Expense(
            id=data["id"],
            description=data["description"],
            amount=float(data["amount"]),
            payer=data["payer"],
            participants={k: float(v) for k, v in data["participants"].items()},
            split_strategy=strat_cls(),  # instantiate strategy
            notes=data.get("notes", ""),
            date=datetime.fromisoformat(data["date"]),
            group_id=data.get("group_id"),
        )

    def _deserialize_settlement(self, data: Dict[str, Any]) -> Settlement:
        """Turn dict back into a Settlement instance (parse ISO date)."""
        return Settlement(
            id=data["id"],
            payer=data["payer"],
            payee=data["payee"],
            amount=float(data["amount"]),
            description=data.get("description", ""),
            date=datetime.fromisoformat(data["date"]),
            notes=data.get("notes", ""),
        )
