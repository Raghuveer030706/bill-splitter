# Run with:  python -m tests.test_day2_manager_demo
# This verifies: expense add → persist → rebuild → settlement → rebuild

from core.models.splits import EqualSplit
from core.models.expense import Expense, Settlement
from core.services.manager import ExpenseManager
from core.services.cache import CacheService

def main():
    # Use a temp store so we don't pollute your real data during tests
    cache = CacheService("data/test_store.json")
    # Reset test file to a clean state
    cache.state = {"users": [], "groups": [], "expenses": [], "settlements": []}
    cache.save()

    mgr = ExpenseManager(cache=cache)

    # you pay 90 for you+sam+lee equally → sam owes you 30, lee owes you 30
    e1 = Expense(
        id="e1",
        description="Dinner",
        amount=90.0,
        payer="you",
        participants={"you": 1, "sam": 1, "lee": 1},
        split_strategy=EqualSplit(),
    )
    mgr.add_expense(e1)
    net_you = mgr.balances_for("you")
    assert net_you["sam"] == -30.0 and net_you["lee"] == -30.0

    # sam pays you back 20
    s1 = Settlement(
        id="s1",
        payer="sam",
        payee="you",
        amount=20.0,
        description="Partial payback"
    )
    mgr.add_settlement(s1)

    # after settlement, sam should only owe 10 now
    net_you = mgr.balances_for("you")
    assert net_you["sam"] == -10.0 and net_you["lee"] == -30.0

    # Totals for dashboard from your perspective:
    you_owe, others_owe_you = mgr.dashboard_totals("you")
    assert you_owe == 0.0 and others_owe_you == 40.0

    print("Manager end-to-end test passed. Current net for you:", net_you)

if __name__ == "__main__":
    main()
