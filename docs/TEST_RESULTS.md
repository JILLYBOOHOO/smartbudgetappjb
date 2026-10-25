# Verification record

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
