# Forward-ref annotations for cleaner type hints
from __future__ import annotations

# defaultdict: nested dict with auto-creation (balance[A][B] pattern)
from collections import defaultdict

# Dict type hint for clarity
from typing import Dict

# Import models for applying domain logic
from .expense import Expense, Settlement


class Ledger:
    """
    Tracks net pairwise balances. balance[A][B] > 0 means A owes B that amount.
    """

    def __init__(self) -> None:
        # Two-level mapping: who owes whom
        self.balance: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

    def apply_expense(self, exp: Expense) -> None:
        """
        For an expense paid by exp.payer, every other participant owes the payer their share.
        """
        alloc = exp.allocations()
        for user, owed in alloc.items():
            if user == exp.payer:
                # Payer does not owe themselves
                continue
            self.balance[user][exp.payer] += owed

    def apply_settlement(self, st: Settlement) -> None:
        """
        A payment from st.payer to st.payee reduces what payer owes payee,
        or reduces what payee owes payer (if the sign flips via netting).
        """
        self.balance[st.payer][st.payee] -= st.amount

    def net_for(self, me: str) -> Dict[str, float]:
        """
        Perspective view: +ve => I owe them; -ve => they owe me.
        Combines both directions for each counterparty.
        """
        result: Dict[str, float] = {}

        # What I owe others
        for other, amt in self.balance.get(me, {}).items():
            if abs(amt) > 1e-9:
                result[other] = amt

        # What others owe me
        for other, mp in self.balance.items():
            if other == me:
                continue
            amt = mp.get(me, 0.0)
            if abs(amt) > 1e-9:
                result[other] = result.get(other, 0.0) - amt

        # Round for display stability
        return {k: round(v, 2) for k, v in result.items()}