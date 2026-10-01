# Known Limitations (Pilot Phase)

## 1. Row-count based watermark assumes strict append-only CSV files
Our extractor tracks "last row count read" per source to detect new entries.
This assumes:
- Existing rows are never edited after being written.
- New rows are only ever appended at the end of the file.

RISK: If a CSV is sorted/filtered AND saved in that sorted state (e.g. in Excel),
row positions change, and this watermark approach will silently skip new rows
or misread old rows as new. No error will be raised.

MITIGATION (not yet implemented): Switch to identity-based deduplication
(e.g. unique key comparison against DB) instead of row-position tracking.
Revisit this when moving to automated/API-based ingestion, or sooner if
manual file edits become a recurring problem.

STATUS: Accepted risk for pilot phase, given manual append-only workflow.


## 2. Inconsistent date formats within the same CSV column
Discovered in Incident_GRC_data.csv: the same 'Date' column contained a mix
of formats -- some rows as MM/DD/YYYY (e.g. "7/27/2026"), others as
MM-DD-YYYY (e.g. "08-03-2026") -- likely from manual edits in different
Excel sessions/locales over time.

CURRENT HANDLING: MetricNormalizer parses dates using pandas format="mixed"
with dayfirst=False, which tolerates both '/' and '-' delimiters as long as
the month-first convention is consistent. Any date that still fails to parse
is logged as a WARNING with the offending raw value(s), rather than failing
silently.

RECOMMENDATION: Where possible, standardize on a single date format
(e.g. always MM/DD/YYYY) across all manually-maintained CSVs going forward,
to avoid ambiguous dates (e.g. "03/04/2026") that NO code can resolve
correctly without knowing the intended convention.

STATUS: Mitigated in code (mixed format tolerant), but true ambiguous dates
remain an unresolvable risk if format inconsistency continues. Flag to data
owners as a process improvement.