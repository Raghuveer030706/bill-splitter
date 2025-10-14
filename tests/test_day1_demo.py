# This small demo script shows how to use the classes interactively
# Run it from terminal:  python tests/test_day1_demo.py

# Import EqualSplit strategy to decide how to divide the total amount
from core.models.splits import EqualSplit

# Import Expense to represent a single transaction
from core.models.expense import Expense

# Import Ledger to record and compute running balances between people
from core.models.ledger import Ledger

# 1️⃣ Choose a splitting rule
splitter = EqualSplit()

# 2️⃣ Create one example expense
exp = Expense(
    id="e1",
    description="Dinner",
    amount=90,
    payer="you",
    participants={"you": 1, "sam": 1, "lee": 1},
    split_strategy=splitter,
)

# 3️⃣ Create a ledger and add the expense
ledger = Ledger()
ledger.apply_expense(exp)

# 4️⃣ Inspect what the system calculates
print("Allocations per person:", exp.allocations())
print("Net for YOU   :", ledger.net_for("you"))   # negative means others owe you
print("Net for SAM   :", ledger.net_for("sam"))   # positive means they owe someone
print("Net for LEE   :", ledger.net_for("lee"))
