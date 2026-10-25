# SmartBudget JA — project report preparation notes

## Project Introduction

SmartBudget JA helps a Jamaican user record JMD income and expenses, compare monthly spending with limits, and track savings allocations. It demonstrates a real Python application with local JSON persistence, uploaded document processing, keyword retrieval and deterministic financial assistance. It is designed for a single-user educational environment and does not connect to a bank.

## Application Screens

1. **Dashboard:** selected-period totals, a six-recorded-month bar chart, category donut, budget versus actual chart, textual chart alternatives, contextual Smart Actions, budget CRUD and savings goals/contributions. Python comprehensions and integer aggregations prepare Plotly figures.
2. **Income & Expenses:** Streamlit forms collect income/expense fields; service validation prevents invalid amounts and missing descriptions. Unique IDs allow updates and confirmed deletion. Lists are filtered by text, type, category and date; pandas exports CSV with spreadsheet formula escaping.
3. **Documents:** `st.file_uploader` accepts PDF/TXT/CSV. pypdf extracts text from unencrypted text PDFs; pandas reads CSV. Generated filenames avoid path traversal. Duplicate file hashes prevent accidental repeat uploads. Extracted content can become a knowledge entry; deletion removes the linked entry. No OCR is claimed.
4. **Knowledge Base:** nine starter topics plus editable user/document sources. Keyword tokens remove common stop words and normalize trailing plurals. Search ranks the proportion of query words overlapping an entry's title/content, returning up to three nonzero matches. This is a transparent retrieval algorithm, not semantic understanding.
5. **Ask SmartBudget:** `st.chat_input`, `st.chat_message`, a spinner, suggestions and session chat history. Recognized money questions call the same calculation services as the dashboard. Education questions return retrieved passages and actual source titles. Unmatched questions receive an explicit fallback.

## Technical Reflection

`st.session_state` keeps navigation, reporting month, appearance, filter widget values and chat across Streamlit reruns. It is not durable storage. Separate JSON collections preserve records on disk. UUIDs identify records. Atomic temporary-file replacements reduce partial-write risk; invalid/corrupt data is preserved with an error. This is not a transactional database and assumes one user/process.

Amounts pass through Decimal rounding and are stored as integer cents; this avoids binary floating-point errors in financial totals. Savings allocations live inside goal records separately from expense transactions, so recording savings does not double-count spending. Plots receive converted amounts only for display.

Actual implementation challenges included distinguishing savings allocations from expenses, preventing corrupt JSON from silently becoming an empty ledger, preventing uploaded filenames from controlling storage paths, and keeping numerical assistant answers independent of text retrieval. Separate functions, generated filenames, explicit accounting labels and preserved-file error handling address these issues. Streamlit AppTest exercises navigation and forms without requiring a graphical browser.

The UI uses native keyboard controls, descriptive labels, a minimum button height, focus outlines and reduced-motion styles. Chart amounts have text/table alternatives. These measures have not been independently audited against every WCAG 2.2 AA requirement.

## Conclusion Notes

The implementation demonstrates Python modules/functions, dictionaries/lists, input validation, Decimal, date filtering, JSON serialization, file I/O, exception handling, third-party libraries, Streamlit reactive state, charts, local document processing, retrieval and automated testing.

Student observations to add:

- [Describe how you installed and ran the application.]
- [Explain one calculation you verified manually.]
- [Describe your own experience testing an uploaded document.]
- [Add actual screenshots using the README walkthrough.]
- [Describe a challenge you personally encountered and what you learned.]
- [Propose a future improvement and explain its tradeoffs.]

Do not present these placeholders as completed personal experiences. Review `TEST_RESULTS.md` for the actual verification record and README for limitations.
