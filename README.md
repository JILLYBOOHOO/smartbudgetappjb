# SmartBudget JA

**Your Money. In Motion.** A local, single-user Jamaican personal finance application for an Amber Heart Academy project. Python 3.11+ and Streamlit; no paid API or external AI service.

## Start on Windows

Open PowerShell in this folder, then run:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the localhost address printed by Streamlit. With an activated environment, the equivalent startup command is `streamlit run app.py`. Stop the server with Ctrl+C.

## Features

- Dashboard: period income, expenses, net cash flow, all-date savings, persisted-data Plotly charts, budget utilization, savings goals and actionable alerts.
- Income & Expenses: add, view, edit, confirm deletion, search, category/type/date filtering, sorting and safe CSV export.
- Documents: local PDF/TXT/CSV validation, extraction, text preview/search, deletion, duplicate detection and linked knowledge entries.
- Knowledge Base: nine educational seed topics, entry CRUD, topic filtering and keyword relevance search with real source titles.
- Ask SmartBudget: deterministic financial answers and retrieved educational passages, suggested questions and session chat history.
- Dark/light appearance, keyboard focus styling, responsive Streamlit columns, native labels, chart text alternatives and reduced-motion CSS.

The stack is Streamlit, pandas, Plotly, pypdf and pytest. Keyword retrieval uses Python's standard library rather than a heavyweight AI dependency.

## Demo and screenshot walkthrough

Click **Load Demo Data** in the sidebar. It adds 32 clearly fictional transactions across four months, one budget and one savings goal. Repeated loading replaces demo-tagged records rather than multiplying them. **Reset Demo Data** requires a checkbox and removes only demo-tagged financial records. Edits to a demo transaction retain its demo label; saving a replacement budget makes that budget your own record.

1. Dashboard: select the current month. Capture summary cards and charts; scroll for budgets and savings. Use the budget editor to create a total or category limit. Saving the same category/month edits its limit.
2. Income & Expenses: show the current-month ledger, or widen the date range for older demo records. Select a transaction below the table to edit or delete it.
3. Documents: upload `assets/fictional-electricity-bill.txt`, click Process document and open its preview. Add to Knowledge Base if desired.
4. Knowledge Base: search “emergency fund” and expand its source entry.
5. Ask SmartBudget: ask “How much did I spend this month?” Capture the actual response. Ask an educational question to show source retrieval.

Use Windows Snipping Tool (Win+Shift+S) to capture the actual browser screens. Screenshots are not bundled or fabricated.

## Accounting and storage

Amounts are validated with Decimal, rounded half-up to cents, then stored and summed as integers. Plotly receives converted display values only. Income minus expenses is **period net cash flow**, not a bank account balance. Record take-home income. Savings contributions are a separate allocation ledger: they do not change income, expenses or net cash flow. Do not also record a savings contribution as an expense unless intentionally treating it as spending. Savings cards sum contributions across all goals/dates, including completed goals. Deleting a goal deletes its history. Budget “All spending” overlaps category limits intentionally and is not added to them.

On first run, `data/` and `data/uploads/` are created. Separate JSON files hold transactions, budgets, goals, document metadata/text, knowledge and initialization settings. Writes use fsync plus atomic replacement. Corrupt or structurally invalid files stop loading with an error and are preserved; manually restore/repair a backup. They are never silently reset. Export all records downloads JSON including extracted text; it does not include original uploaded files. For a full backup, stop the app and copy the entire `data` directory. There is no import UI. To restore, stop the app and replace the folder with the backed-up folder.

UI navigation, selected month, filters, theme and chat use `st.session_state`; they are temporary. Financial records survive restarts. Set `SMARTBUDGET_DATA` to a dedicated folder to change storage location.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Tests cover cents precision; income/expenses/balance/category/month calculations; budget utilization; savings; storage edits, deletion, restart and corruption; retrieval; text/CSV/PDF handling; alerts; demo idempotence; financial answers; all five screens, navigation, theme switching and transaction form persistence through Streamlit AppTest. See `docs/TEST_RESULTS.md` for results from this build.

## Limits

This is educational software, not banking infrastructure. Files are local and unencrypted. No login, account synchronization, tax calculation, currency conversion, production concurrency control or financial advice engine is included. Use one app process and one user at a time. Scanned/encrypted PDFs and OCR are unsupported. UTF-8 is required for TXT/CSV; files are limited to 10 MB, PDFs to 100 pages and extracted text to one million characters. A malicious or unusually complex PDF may still consume processing time; use trusted school documents.

The assistant recognizes a documented set of financial question patterns; other questions use keyword overlap and may return several source excerpts rather than a generated synthesis. Document content is treated as text, never instructions. No transactions are automatically created from uploads. “This month”/“last month” use the local Python system date; other questions use the reporting month. Configure your computer's local timezone correctly.

Charts and hover/progress effects are restrained. Smooth financial number tweening is not implemented; native Streamlit metrics update accurately after reruns. Light mode overrides major app surfaces but some native widgets may retain the configured dark base. Accessibility practices are implemented; formal WCAG 2.2 AA certification and physical mobile-device/browser assistive-technology audits have not been performed. The five referenced inspiration images were not present in the provided attachment; the written palette drove the design.
