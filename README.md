# Bill Splitter (Streamlit + Python OOP)
## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/app.py

One-week plan recap (fit to your repo/IDE)
Day 1: OOP models + split strategies + unit tests.
Day 2: Services (auth, cache, manager) + tests.
Day 3: UI skeleton (login → dashboard placeholders).
Day 4: Record Expense modal (save → refresh dashboard).
Day 5: Settle modal (apply → refresh).
Day 6: Validations, empty states, logout, theme.
Day 7: QA, demo data, README polish, PR merge.


bill-splitter/
├── app/
│   ├── app.py
│   ├── components/
│   └── pages/
├── core/
│   ├── models/
│   │   ├── user.py
│   │   ├── group.py
│   │   ├── expense.py
│   │   ├── splits.py
│   │   └── ledger.py
│   ├── services/
│   │   ├── auth.py
│   │   ├── cache.py
│   │   └── manager.py
│   └── utils/dates.py
├── data/
│   └── store.json
├── tests/
├── requirements.txt
├── .streamlit/
│   └── config.toml
└── README.md

| Day   | Focus           | Deliverables                                                                              |
| ----- | --------------- | ----------------------------------------------------------------------------------------- |
| **1** | Core OOP Models | Implement `User`, `Expense`, `Settlement`, `Ledger`, and Split Strategies with unit tests |
| **2** | Services        | Build `AuthService`, `CacheService`, `ExpenseManager`                                     |
| **3** | UI Skeleton     | Streamlit Login + Dashboard layout (stub buttons)                                         |
| **4** | Record Expense  | Full popup, add to cache, refresh dashboard                                               |
| **5** | Settle Popup    | Record payment, clear balances                                                            |
| **6** | Validation + UX | Notes, toasts, logout, theming                                                            |
| **7** | QA + GitHub     | Test, polish README, demo dataset, push to GitHub                                         |
