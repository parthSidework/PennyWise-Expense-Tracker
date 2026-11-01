import sqlite3
from datetime import date, datetime
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

DB_PATH = Path(__file__).with_name("expenses.db")
CATEGORIES = ["Food", "Transport", "Shopping", "Bills", "Education", "Health", "Entertainment", "Other"]

def connect():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            category TEXT NOT NULL,
            spent_on TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            note TEXT DEFAULT ''
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL,
            category TEXT NOT NULL,
            limit_amount REAL NOT NULL CHECK(limit_amount > 0),
            UNIQUE(month, category)
        )""")

def add_expense(title, amount, category, spent_on, payment_method, note):
    with connect() as con:
        con.execute("INSERT INTO expenses(title, amount, category, spent_on, payment_method, note) VALUES(?,?,?,?,?,?)",
                    (title.strip(), float(amount), category, spent_on.isoformat(), payment_method, note.strip()))

def get_expenses():
    with connect() as con:
        return pd.read_sql_query("SELECT * FROM expenses ORDER BY spent_on DESC, id DESC", con)

def delete_expense(expense_id):
    with connect() as con:
        con.execute("DELETE FROM expenses WHERE id=?", (int(expense_id),))

def save_budget(month, category, amount):
    with connect() as con:
        con.execute("""INSERT INTO budgets(month, category, limit_amount) VALUES(?,?,?)
        ON CONFLICT(month, category) DO UPDATE SET limit_amount=excluded.limit_amount""",
                    (month, category, float(amount)))

def get_budgets(month):
    with connect() as con:
        return pd.read_sql_query("SELECT category, limit_amount FROM budgets WHERE month=?", con, params=(month,))

st.set_page_config(page_title="PennyWise | Expense Tracker", page_icon="💸", layout="wide")
init_db()
st.title("💸 PennyWise — Expense Tracker & Budget Manager")
st.caption("A student-friendly personal finance dashboard built with Python, Streamlit and SQLite.")

with st.sidebar:
    st.header("Navigation")
    page = st.radio("Choose a section", ["Dashboard", "Add Expense", "Manage Budget", "Transactions", "About"])
    st.divider()
    st.caption("Data is stored locally in expense_tracker/expenses.db.")

df = get_expenses()
today = date.today()
month_key = today.strftime("%Y-%m")
month_df = df[df["spent_on"].str.startswith(month_key)] if not df.empty else df
month_total = float(month_df["amount"].sum()) if not month_df.empty else 0.0
all_total = float(df["amount"].sum()) if not df.empty else 0.0

if page == "Dashboard":
    st.subheader("Your financial overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Spent this month", f"₹{month_total:,.2f}")
    c2.metric("All-time spending", f"₹{all_total:,.2f}")
    c3.metric("Transactions", int(len(df)))
    if not month_df.empty:
        left, right = st.columns(2)
        category_data = month_df.groupby("category", as_index=False)["amount"].sum()
        left.plotly_chart(px.pie(category_data, names="category", values="amount", hole=.45,
                                 title="Monthly spending by category"), use_container_width=True)
        daily = month_df.copy()
        daily["spent_on"] = pd.to_datetime(daily["spent_on"])
        daily_data = daily.groupby("spent_on", as_index=False)["amount"].sum()
        right.plotly_chart(px.bar(daily_data, x="spent_on", y="amount", title="Daily spending"),
                           use_container_width=True)
        budgets = get_budgets(month_key)
        if not budgets.empty:
            st.subheader("Budget status")
            actual = month_df.groupby("category", as_index=False)["amount"].sum()
            status = budgets.merge(actual, on="category", how="left").fillna({"amount": 0})
            for _, row in status.iterrows():
                limit = float(row["limit_amount"])
                spent = float(row["amount"])
                st.write(f"**{row['category']}** — ₹{spent:,.2f} of ₹{limit:,.2f}")
                st.progress(min(spent / limit, 1.0))
                if spent > limit:
                    st.error(f"Budget exceeded by ₹{spent-limit:,.2f}")
                elif spent >= limit * .8:
                    st.warning("You have used at least 80% of this budget.")
                else:
                    st.success("Within budget.")
    else:
        st.info("No expenses recorded for this month. Add your first transaction to see insights.")
    if not df.empty:
        st.subheader("Recent transactions")
        st.dataframe(df.head(5), use_container_width=True, hide_index=True)

elif page == "Add Expense":
    st.subheader("Record a new expense")
    with st.form("expense_form", clear_on_submit=True):
        title = st.text_input("Description", placeholder="e.g. Lunch at college")
        a, b = st.columns(2)
        amount = a.number_input("Amount (₹)", min_value=0.01, value=100.0, step=10.0)
        category = b.selectbox("Category", CATEGORIES)
        c, d = st.columns(2)
        spent_on = c.date_input("Date", value=today)
        payment = d.selectbox("Payment method", ["UPI", "Cash", "Card", "Net Banking", "Other"])
        note = st.text_area("Note (optional)")
        submitted = st.form_submit_button("Save expense", type="primary")
        if submitted:
            if not title.strip():
                st.error("Please enter a description.")
            elif amount <= 0:
                st.error("Amount must be greater than zero.")
            else:
                add_expense(title, amount, category, spent_on, payment, note)
                st.success("Expense saved successfully.")
                st.rerun()

elif page == "Manage Budget":
    st.subheader("Set monthly category budgets")
    selected_month = st.date_input("Choose any date in the target month", value=today).strftime("%Y-%m")
    with st.form("budget_form"):
        category = st.selectbox("Category", CATEGORIES)
        limit = st.number_input("Monthly limit (₹)", min_value=1.0, value=1000.0, step=100.0)
        save = st.form_submit_button("Save budget")
        if save:
            save_budget(selected_month, category, limit)
            st.success("Budget saved or updated.")
    budgets = get_budgets(selected_month)
    if not budgets.empty:
        st.dataframe(budgets, use_container_width=True, hide_index=True)
    else:
        st.info("No budgets have been set for this month.")

elif page == "Transactions":
    st.subheader("Transaction history")
    if df.empty:
        st.info("No transactions yet.")
    else:
        search = st.text_input("Search description or category")
        filtered = df.copy()
        if search:
            mask = (filtered["title"].str.contains(search, case=False, na=False) |
                    filtered["category"].str.contains(search, case=False, na=False))
            filtered = filtered[mask]
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button("Download transactions as CSV", csv, "expense_transactions.csv", "text/csv")
        ids = filtered["id"].tolist()
        if ids:
            selected_id = st.selectbox("Select transaction ID to delete", ids)
            if st.button("Delete selected transaction"):
                delete_expense(selected_id)
                st.success("Transaction deleted.")
                st.rerun()

else:
    st.subheader("About this project")
    st.markdown("""
    **PennyWise** is a mini personal-finance application created as a Python Project-Based Learning (PBL) project.

    **Core features**
    - Record, view, search and delete expenses.
    - Categorise spending and review monthly totals.
    - Set monthly budgets by category.
    - View charts and budget warnings.
    - Export transaction data to CSV.

    **Technology:** Python, Streamlit, SQLite, Pandas and Plotly.

    **Privacy note:** This classroom version stores data in a local SQLite database. It is not a bank,
    does not connect to payment accounts and should not be used to store sensitive financial credentials.
    """)
