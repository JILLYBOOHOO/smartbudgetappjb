# Verification record

## Premium UI redesign

31 tests passed in 40.04 seconds. The full regression suite plus global-search/month-navigation coverage passed. Actual browser checks covered all five screens in both themes at 1440px and the dashboard at seven requested widths in both themes. A 320px billion-dollar-value fixture remained fully visible. All six existing user JSON files were byte-for-byte unchanged. See UI_REDESIGN.md for verification scope and limits.

## Compact entry and bank-statement revision

**30 tests passed in 33.94 seconds.** Added tests for merchant-based category suggestions and manual overrides; debit/credit bank CSV parsing; exclusion of opening balances and running balances; PDF-extracted text row parsing; date-order selection; ambiguous direction flags; unsupported row handling; statement preview analysis, confirmed import and duplicate prevention. Existing quick-entry, upload, finance and storage tests also passed. Bank statement UI tests use an injected uploader file fixture, not the operating-system file chooser.

Entry fields now use two-column rows with a separate optional-details tab. The popup's actual layout is checked in the running browser. This does not claim every device/zoom/keyboard combination will fit without scrolling. Bank PDFs are parsed heuristically from extracted text; complex/wrapped layouts may require CSV. Full dates and decimal monetary values are required for PDF/TXT rows. Scanned PDFs remain unsupported; there is no OCR. All statement previews and summaries are local. Only explicitly included and confirmed rows are imported.

## Usability revision

**24 tests passed in 27.97 seconds** after the quick-entry and upload redesign. The full suite includes the original financial/storage checks plus one-line amount/category/date suggestions, receipt-total detection, CSV row validation, optional income source and description, saving from the quick popup, budget and savings Smart Action popup saves, reviewed document-to-transaction creation, reviewed CSV import and duplicate-import prevention. Upload UI tests inject a BytesIO fixture at the uploader boundary and exercise the actual preview/save controls; they do not automate the operating-system file chooser.

The running browser was checked for the simplified controls and compact popup, including dismissal. A screenshot of the actual revised quick-entry popup is supplied alongside the project ZIP. No test records were added to the user's ledger. A bug found during testing where a budget popup lost its open state before saving was corrected. A receipt parser bug matching “total” inside “subtotal” was also corrected. On this Windows sandbox the UI test runner needed loopback network access; early stalled runs were stopped and the final full run passed.

Photos/scanned PDFs still have no OCR support. Text-based PDF/TXT/CSV is supported. Suggestions are local deterministic extraction, not a language model. New one-line and document paths always require a reviewed Save or Import action before recording financial data.

## Initial build

Tested on Windows with Python 3.14.7, Streamlit 1.66.1, pandas 3.1.0, Plotly 6.9.0, pypdf 6.21.2 and pytest 9.1.1.

**16 tests passed in 37.70 seconds.** Two non-failing pandas forward-compatibility warnings occurred while choosing text columns for CSV export. Python compilation also passed.

The local Streamlit HTTP server started successfully at 127.0.0.1:8501 and its health endpoint returned `ok`. The workspace-target dependency installation caused Streamlit to infer development mode; explicitly disabling that mode allowed normal packaged-server startup. The README virtual environment installation avoids this target-install layout.

Automated checks included:

- Exact cents, half-up rounding and invalid monetary input.
- Income, expenses, cash flow, category totals and monthly selection.
- Atomic JSON persistence, update without duplication, delete and a new Store instance reading saved data.
- Invalid/corrupt data rejection with original file preservation.
- Budget utilization and threshold Smart Actions; empty-period and near-complete savings conditions.
- Goal contribution totals.
- Knowledge relevance ranking, unknown-query fallback and source-bearing assistant answers.
- TXT and CSV extraction; invalid extension, invalid bytes, oversized/empty files and invalid PDF errors.
- A generated text PDF extracts successfully; a blank PDF explicitly reports no OCR.
- Four-month demo totals and repeated-load idempotence.
- Streamlit AppTest loads all five screens and navigates between them, including light mode.
- The transaction form writes a persisted integer-cent record; a fresh app instance loads without exception.
- Budget creation, goal creation, contribution recording and knowledge entry creation/search through actual Streamlit widgets.
- Suggested chat questions produce a sourced response and retain history.
- Demo reset is disabled until confirmed and preserves a personal savings goal.
- Invalid transaction form submission displays an error and writes no record.

The first dependency/test attempts hit restricted OS temporary directories. Installation and tests succeeded after directing temporary storage into the workspace. The successful run used `python -m pytest -q --basetemp ../../work/pytest-run` with the installed dependency folder on PYTHONPATH. A normal local virtual environment uses the README commands directly.

Limitations of verification: AppTest runs Streamlit's actual Python widgets and state but does not provide a browser pixel/layout, screen reader, keyboard traversal or physical mobile test. File uploader processing is tested at the service layer; native browser file selection and downloads have not been automated. No WCAG conformance claim is made. Chart rendering code loaded successfully using persisted demo data; hover interactions were not browser-tested. Smooth metric-number tweening is not implemented. There were no inspiration images in the supplied attachment.
