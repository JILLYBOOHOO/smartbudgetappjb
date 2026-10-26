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

## Compact entry and bank statements

The popup has two-column **Quick entry** fields and an **Extra details** tab, so optional fields do not lengthen the form. Typing or changing a description updates a visible category suggestion when you press Enter or leave the field. Leave Category on Auto-detect, or select a category to override it. Rules recognize examples such as MegaMart/PriceSmart groceries, JPS electricity, NWC water, payroll and taxi/fuel expenses. Unknown descriptions remain Other; these are deterministic suggestions rather than AI certainty.

Upload a bank statement in **Documents**, then choose **Bank statement** (selected automatically for recognizable statement headers/names). Text-based PDF/TXT and bank CSV exports are supported. Bank CSV columns can include Date/Transaction Date, Description/Details, Debit/Withdrawal and Credit/Deposit; a signed Amount and optional Type/DR-CR column is also supported. Choose day-first or month-first dates. A running Balance column is never recorded as income or spending.

The preview lets you edit descriptions, dates, amounts, categories and money direction, and exclude rows with Include. Uncertain money directions start excluded. Review the included income/expense/category totals, confirm the checkbox and click Import bank statement. Imported-file hashes block duplicates. Extraction notes report skipped dated rows; no parser claims to handle every bank layout. Use a CSV export if a PDF has wrapped descriptions, multiple monetary columns or unsupported dates. Opening/closing balance summary rows are excluded.

PDF/TXT rows must contain a full date, description, transaction amount with two decimal places, optional DR/CR marker, and at most one trailing running balance. Layout extraction is heuristic: verify amounts and directions against the original. Photos/scanned PDFs still need OCR, which is not implemented. Statement amounts are interpreted as JMD; foreign-currency statements are unsupported. Files stay local.

Try the clearly fictional `assets/sample-bank-statement.csv` or `.txt` to see categorization and statement analysis without real banking details.

## Faster everyday recording

Use **Add money** or **Add spending** to open a compact popup. Only the amount is required. A description, income source, payment method, category, date and notes can be adjusted but are optional; blank descriptions get a sensible label. Open “Type a sentence instead” for entries such as `Spent 2500 on groceries yesterday` or `Made 35k from a freelance client`. These are local keyword/amount suggestions, always reviewed before saving.

**Upload receipt or bill** accepts text PDFs, TXT and CSV. Uploads are extracted locally. A bill or invoice can suggest a total, category and date for a reviewed transaction. Store the document, check the suggestions, then save the transaction. Unpaid invoices should be stored as documents rather than recorded as money received/spent. Duplicate linked receipts are blocked from adding another transaction.

CSV transaction imports require an `amount` or `amount_jmd` column in JMD. Optional columns: `date` (YYYY-MM-DD), `description`, `type` (Income/Expense), `category`. Other categories map to Other. Without a type, rows default to Expense; negative amounts also default to Expense. Review the preview and confirm the import; no silent financial writes occur. Re-importing the same file is blocked while its imported transactions exist.

Photos/scanned PDFs still require OCR and are not supported. Export a text-based PDF or enter its amount using the popup.

## Features

- Dashboard: period income, expenses, net cash flow, all-date savings, persisted-data Plotly charts, budget utilization, savings goals and actionable alerts.
- Income & Expenses: add, view, edit, confirm deletion, search, category/type/date filtering, sorting and safe CSV export.
- Documents: local PDF/TXT/CSV validation, extraction, text preview/search, deletion, duplicate detection and linked knowledge entries.
- Knowledge Base: nine educational seed topics, entry CRUD, topic filtering and keyword relevance search with real source titles.
- Ask SmartBudget: deterministic financial answers and retrieved educational passages, suggested questions and session chat history.
- Dark/light appearance, keyboard focus styling, responsive Streamlit columns, native labels, chart text alternatives and reduced-motion CSS.

The stack is Streamlit, pandas, Plotly, pypdf and pytest. Keyword retrieval uses Python's standard library rather than a heavyweight AI dependency.

## Your records and screenshots

The application has no demo-data controls and does not seed financial records. Add your own transactions with Add Income/Add Expense, or review a bill, receipt or statement through Documents. Imported amounts must be in the currency supported by the app (currently JMD); do not relabel foreign-currency amounts as JMD.

For school screenshots, show the actual application screens with records you are authorized to use. Select the matching reporting month for historical records. Redact personal information before sharing screenshots. The knowledge base's educational starter entries are separate from financial records.

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
