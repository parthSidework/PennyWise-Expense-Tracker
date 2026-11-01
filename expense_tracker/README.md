# PennyWise — Expense Tracker & Budget Management

A Python PBL project to record daily expenses, set monthly budgets, analyse spending and export transactions.

## Features
- Add expenses with date, category, payment method and note
- Dashboard with monthly/all-time totals and charts
- Monthly budgets by category with 80% and over-budget alerts
- Search, view and delete transactions
- Export filtered transactions to CSV
- Local SQLite database (no external database account required)

## Tech stack
Python 3.10+, Streamlit, SQLite, Pandas, Plotly.

## Run locally
```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the application
streamlit run app.py
```
Open the local URL shown in the terminal (normally http://localhost:8501).
The database `expenses.db` is created automatically beside `app.py`.

## GitHub upload
```bash
git init
git add .
git commit -m "Initial PennyWise expense tracker project"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/pennywise-expense-tracker.git
git push -u origin main
```
Create an empty public repository on GitHub first, then replace `YOUR-USERNAME` above.

## Project structure
```text
expense-tracker-pbl/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── docs/
    └── project-report.pdf
```

## Limitations and future scope
This educational version is local and single-user. Future improvements could include authentication, cloud database,
recurring transactions, receipt uploads, mobile support and encrypted backups.
