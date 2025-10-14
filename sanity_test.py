from core.models.expense import Expense
from core.models.splits import EqualSplit

e = Expense(
    id="t1",
    description="Test",
    amount=10.0,
    payer="you",
    participants={"you": 1, "sam": 1},
    split_strategy=EqualSplit(),
)
print("OK:", e.date)
