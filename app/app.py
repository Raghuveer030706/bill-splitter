# -----------------------------
# Streamlit UI shell for Day 3
# -----------------------------
# Imports (with purpose):
# - streamlit as st: UI framework
# - typing: clean signatures
# - datetime: display timestamps in the activity table
# - local services: use your orchestrator to fetch balances & persist later
import sys, os
# Ensure parent directory (project root) is on Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from typing import Dict, Any, Tuple

from core.services.manager import ExpenseManager
from core.services.auth import AuthService
from core.utils.money import fmt, qround, EPS

from datetime import datetime
from core.models.splits import EqualSplit, ExactSplit, ShareSplit
from core.models.expense import Expense
from core.models.expense import Settlement  # NEW
import uuid  # for unique IDs

# ---- Page config: title, favicon, layout
st.set_page_config(page_title="Bill Splitter", page_icon="💸", layout="wide")

# ---- One-time app services: build once and keep around
# We store manager & auth in session so they persist across reruns
if "services" not in st.session_state:
    st.session_state.services = {
        "auth": AuthService(),
        "mgr": ExpenseManager(),  # reads data/store.json if present
    }

if "ui" not in st.session_state:
    st.session_state.ui = {"currency": "₹"}  # default

with st.sidebar:
    st.markdown("### Settings")
    cur = st.selectbox("Currency", ["₹", "$", "€", "£", "Custom…"], index=0)
    if cur == "Custom…":
        cur = st.text_input("Symbol", value=st.session_state.ui["currency"])
    st.session_state.ui["currency"] = cur
    st.caption("Affects display only; calculations remain numeric.")

auth: AuthService = st.session_state.services["auth"]
mgr: ExpenseManager = st.session_state.services["mgr"]

# ---- Session auth state
if "auth_state" not in st.session_state:
    st.session_state.auth_state = {"logged_in": False, "username": None}

# ---- Helper: simple guard for login state
def require_login() -> bool:
    return bool(st.session_state.auth_state["logged_in"] and st.session_state.auth_state["username"])

# ---- UI: Top nav bar (appears only when logged in)
def app_header():
    left, right = st.columns([3, 1])
    with left:
        st.subheader("💸 Bill Splitter — Dashboard")
    with right:
        user = st.session_state.auth_state["username"]
        if user:
            st.caption(f"Signed in as **{user}**")
            if st.button("Logout", use_container_width=True):
                st.session_state.auth_state = {"logged_in": False, "username": None}
                st.success("Logged out.")
                st.rerun()

# ---- Login view
def login_view():
    st.title("Welcome to Bill Splitter 💸")
    st.markdown("Sign in to track shared expenses and balances.")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username (email)")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True)
        if submitted:
            if auth.login(username, password):
                st.session_state.auth_state = {"logged_in": True, "username": username}
                st.success("Login successful! Redirecting to dashboard…")
                st.rerun()
            else:
                st.error("Invalid credentials. Try again.")

    # Forgot password stub for Day 3 (no email): we just show a friendly message
    if st.button("Forgot password?"):
        st.info(auth.forgot_password("any@demo"))

    # Helpful demo creds
    with st.expander("Demo accounts (for testing)"):
        st.code("you@example.com / pass123\nsam@example.com / pass123", language="text")

# ---- Dashboard cards: What you owe vs Others owe you
def dashboard_cards(username: str):
    # manager provides totals already aggregated
    you_owe, others_owe_you = mgr.dashboard_totals(username)
    c = st.session_state.ui["currency"]

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1: st.metric("You Owe", fmt(you_owe, c))
    with c2: st.metric("Others Owe You", fmt(others_owe_you, c))
    with c3:
        # Action buttons (placeholders for Day 4/5)
        b1, b2 = st.columns(2)
        with b1:
            if st.button("➕ Record expense", key="btn_record_expense", help="Add a shared expense"):
                open_record_expense(username)
        with b2:
            if st.button("✅ Settle", key="btn_settle", help="Record a payment with a counterparty"):
                open_settle_dialog(username)

# ---- Balances table: pairwise net amounts for the current user
def balances_table(username: str):
    st.markdown("### Your balances (pairwise)")
    net: Dict[str, float] = mgr.balances_for(username)
    if not net:
        st.info("No balances yet. Use **Record expense** to add your first item.")
        return

    # Render simple table: positive => you owe them; negative => they owe you
    rows = []
    for other, amt in sorted(net.items(), key=lambda x: x[0].lower()):
        status = "You owe" if amt > 0 else "Owes you"
        # balances_table
        rows.append({"Counterparty": other, "Amount": fmt(abs(amt), st.session_state.ui["currency"]),
                     "Direction": "You owe" if amt > 0 else "Owes you"})

    st.table(rows)

# ---- Recent activity (lightweight Day 3: show raw cached dicts)
def recent_activity():
    st.markdown("### Recent activity")
    # For Day 3, we’ll just read raw cache dicts; we’ll pretty this up later
    exps = mgr.cache.list_expenses()
    sets = mgr.cache.list_settlements()

    # Coalesce into a single timeline
    events = []
    for e in exps:
        events.append({
            "when": e.get("date"),
            "type": "Expense",
            "who": e.get("payer"),
            "desc": e.get("description"),
            "amount": e.get("amount"),
        })
    for s in sets:
        events.append({
            "when": s.get("date"),
            "type": "Settlement",
            "who": f'{s.get("payer")} → {s.get("payee")}',
            "desc": s.get("description"),
            "amount": s.get("amount"),
        })

    if not events:
        st.caption("No activity yet.")
        return

    # Sort newest first
    events.sort(key=lambda x: x["when"] or "", reverse=True)

    # Render compact
    for ev in events[:10]:
        with st.container(border=True):
            tag = "🧾 Expense" if ev["type"] == "Expense" else "✅ Settlement"
            st.write(f'{tag} • {ev["who"]} • {fmt(float(ev["amount"]), st.session_state.ui["currency"])}')
            if ev.get("desc"): st.caption(ev["desc"])
            if ev.get("when"): st.caption(ev["when"])

def open_settle_dialog(username: str):
    """
    'Settle up' dialog with dynamic counterparty selection.
    The counterparty selector is rendered outside the form so changes take effect immediately.
    """
    mgr: ExpenseManager = st.session_state.services["mgr"]

    # Always compute the latest balances
    net = mgr.balances_for(username)
    counterparties = sorted([k for k, v in net.items() if abs(v) > EPS])

    # If no one to settle with, bail early (works in dialog or inline)
    def _no_cp_ui():
        st.info("No counterparties found. Add an expense first.")
        if hasattr(st, "dialog"):
            # show a close-ish action in newer Streamlit; or just return
            pass

    # ---- Counterparty selector OUTSIDE the form (so it reruns immediately)
    if not counterparties:
        if hasattr(st, "dialog"):
            st.dialog("Settle up")(_no_cp_ui)()
        else:
            st.markdown("## Settle up")
            _no_cp_ui()
        return

    # Persist selected counterparty in session state
    if "settle_counterparty" not in st.session_state or st.session_state.settle_counterparty not in counterparties:
        st.session_state.settle_counterparty = counterparties[0]

    def _header_and_selector():
        st.caption("Pick the person you’re settling with. Changing this updates the form below instantly.")
        st.selectbox(
            "Counterparty",
            options=counterparties,
            index=counterparties.index(st.session_state.settle_counterparty),
            key="settle_counterparty",
            help="This control is outside the form so it re-runs immediately."
        )

    # ---- The form body (reads current counterparty from session state)
    def _render_form():
        other = st.session_state.settle_counterparty
        with st.form("settle_form", clear_on_submit=False):
            current = float(net.get(other, 0.0))
            dir_hint = "You owe them" if current > 0 else "They owe you"
            st.write(f"**Current balance with {other}:** {dir_hint} **{fmt(abs(current), st.session_state.ui['currency'])}**")

            # Who pays whom? Infer from sign but allow override
            default_payer = username if current > 0 else other
            payer = st.radio(
                "Who is paying now?",
                options=[username, other],
                index=0 if default_payer == username else 1,
                horizontal=True,
            )
            payee = other if payer == username else username

            # Default amount = outstanding (clamped to >= 0)
            outstanding = abs(current)
            amount = st.number_input(
                "Payment amount",
                min_value=0.0,
                value=float(qround(outstanding)) if outstanding > 0 else 0.0,
                step=0.01,
                format="%.2f",
            )

            description = st.text_input("Description", placeholder="Payback for dinner")
            notes = st.text_area("Notes (optional)", placeholder="Any context to remember…")

            # Disable while saving
            disabled = st.session_state.get("busy", False)
            submitted = st.form_submit_button("Save", type="primary", use_container_width=True, disabled=disabled)

            if submitted:
                errors = []
                if amount <= 0:
                    errors.append("Amount must be greater than zero.")
                # prevent accidental overpay by > 1 cent
                if outstanding > 0 and (amount - outstanding) > (0.01 + EPS):
                    errors.append("Payment exceeds current outstanding balance.")
                if payer == payee:
                    errors.append("Payer and payee cannot be the same.")

                if errors:
                    for e in errors:
                        st.error(e)
                    st.stop()

                st_obj = Settlement(
                    id=f"s_{uuid.uuid4().hex[:8]}",
                    payer=payer,
                    payee=payee,
                    amount=float(amount),
                    description=description.strip(),
                    notes=notes.strip(),
                )

                # Disable submit while saving + toasts
                if "busy" not in st.session_state:
                    st.session_state.busy = False

                if st.session_state.busy:
                    st.info("Processing… Please wait.")
                else:
                    st.session_state.busy = True
                    try:
                        mgr.add_settlement(st_obj)
                        if hasattr(st, "toast"):
                            st.toast("Settlement recorded ✅", icon="💰")
                        st.success("Settlement recorded successfully!")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Failed to record settlement: {ex}")
                    finally:
                        st.session_state.busy = False

    # ---- Render as dialog if available; otherwise inline
    if hasattr(st, "dialog"):
        @st.dialog("Settle up")
        def _dialog():
            _header_and_selector()   # selector OUTSIDE the form
            _render_form()           # form reads current selection
        _dialog()
    else:
        st.markdown("## Settle up")
        _header_and_selector()
        _render_form()

def open_record_expense(username: str):
    """
    Renders a 'Record expense' form.
    If Streamlit supports st.dialog, show it as a dialog; otherwise render inline.
    """
    mgr = st.session_state.services["mgr"]

    # The form UI as a function so we can use it with st.dialog decorator or inline
    def _render_form():

        # --- Split type selector OUTSIDE the form so it re-runs immediately ---
        if "split_type" not in st.session_state:
            st.session_state.split_type = "Equal"

        st.selectbox(
            "How to split?",
            options=["Equal", "Exact amounts", "Shares (weights/percent)"],
            index=["Equal", "Exact amounts", "Shares (weights/percent)"].index(st.session_state.split_type),
            key="split_type",
            help="Changing this will update the fields below immediately."
        )

        with st.form("record_expense_form", clear_on_submit=False):
            st.caption("Add a shared expense with one other person. Date defaults to now.")

            col_a, col_b = st.columns(2)
            with col_a:
                you = st.text_input("You (email)", value=username, disabled=True)
            with col_b:
                other = st.text_input("Other person (email)", placeholder="sam@example.com")

            description = st.text_input("Description", placeholder="Dinner at Bistro")
            amount = st.number_input("Total amount", min_value=0.0, step=0.01, format="%.2f")

            payer = st.radio(
                "Who paid?",
                options=[you, other] if other else [you],
                index=0,
                horizontal=True,
                disabled=not other,
            )

            current_split = st.session_state.split_type

            exact_you = exact_other = share_you = share_other = None
            if current_split == "Exact amounts":
                col1, col2 = st.columns(2)
                with col1:
                    exact_you = st.number_input(f"Exact for {you}", min_value=0.0, step=0.01, format="%.2f")
                with col2:
                    exact_other = st.number_input(f"Exact for {other or 'Other'}", min_value=0.0, step=0.01, format="%.2f")
            elif current_split == "Shares (weights/percent)":
                col1, col2 = st.columns(2)
                with col1:
                    share_you = st.number_input(f"Share for {you}", min_value=0.0, step=1.0, format="%.0f", help="e.g., 1, 2, 50")
                with col2:
                    share_other = st.number_input(f"Share for {other or 'Other'}", min_value=0.0, step=1.0, format="%.0f")

            notes = st.text_area("Notes (optional)", placeholder="Any notes to remember…")

            groups = mgr.cache.state.get("groups", [])
            group_names = ["(none)"] + [f'{g["id"]}:{g["name"]}' for g in groups]
            chosen = st.selectbox("Add to existing group", options=group_names, index=0)
            new_group_name = st.text_input("…or create a new group", placeholder="Trip to NYC")

            submitted = st.form_submit_button("Save", type="primary", use_container_width=True)

            if submitted:
                errors = []
                if not other:
                    errors.append("Please enter the other person's email.")
                if not description:
                    errors.append("Please enter a description.")
                if amount <= 0:
                    errors.append("Amount must be greater than zero.")
                if other == you:
                    errors.append("The other person must be different from you.")

                participants = {you: 1.0, other or "": 1.0}
                strategy = EqualSplit()

                if current_split == "Exact amounts":
                    if exact_you is None or exact_other is None:
                        errors.append("Please enter both exact amounts.")
                    else:
                        if round((exact_you + exact_other) - amount, 2) != 0.00:
                            errors.append("Exact amounts must sum to the total.")
                        participants = {you: float(exact_you), other: float(exact_other)}
                        strategy = ExactSplit()

                elif current_split == "Shares (weights/percent)":
                    if (share_you or 0) <= 0 or (share_other or 0) <= 0:
                        errors.append("Shares must be positive numbers.")
                    else:
                        participants = {you: float(share_you), other: float(share_other)}
                        strategy = ShareSplit()

                group_id = None
                if new_group_name.strip():
                    gid = f"g_{uuid.uuid4().hex[:8]}"
                    mgr.cache.add_group(gid, new_group_name.strip())
                    group_id = gid
                elif chosen != "(none)":
                    group_id = chosen.split(":")[0]

                if errors:
                    for e in errors:
                        st.error(e)
                    st.stop()

                exp = Expense(
                    id=f"e_{uuid.uuid4().hex[:8]}",
                    description=description.strip(),
                    amount=float(amount),
                    payer=payer,
                    participants=participants,
                    split_strategy=strategy,
                    notes=notes.strip(),
                    group_id=group_id,
                    date=datetime.utcnow(),
                )

                # --- Disable submit while saving + toast feedback ---
                if "busy" not in st.session_state:
                    st.session_state.busy = False

                if st.session_state.busy:
                    st.info("Processing… Please wait.")
                else:
                    st.session_state.busy = True
                    try:
                        mgr.add_expense(exp)
                        if hasattr(st, "toast"):
                            st.toast("Expense saved ✅", icon="💾")
                        st.success("Expense saved successfully!")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Failed to save expense: {ex}")
                    finally:
                        st.session_state.busy = False

    # If st.dialog exists, use it as a decorator; otherwise render inline
    if hasattr(st, "dialog"):
        # st.dialog returns a decorator; apply it to our form function, then call it
        st.dialog("Record expense")(_render_form)()
    else:
        st.markdown("## Record expense")
        _render_form()

# ---- Main router
def main():
    if not require_login():
        login_view()
        return

    # Logged-in content
    app_header()
    user = st.session_state.auth_state["username"]

    dashboard_cards(user)
    st.divider()
    balances_table(user)
    st.divider()
    recent_activity()

if __name__ == "__main__":
    main()
