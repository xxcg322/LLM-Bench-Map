# Analysis outputs

Start with [OVERVIEW.md](OVERVIEW.md) for counts and matched-year comparisons,
[METHODS.md](METHODS.md) for definitions, and [RESULTS_NOTES.md](RESULTS_NOTES.md)
for a concise guide to findings. `claim_ledger.csv` links each finding to its data
and selector; `CAPTIONS.md` explains the figures and tables.

Run `python reproduce.py` from the repository root. Use `--output reproduced` to
keep regenerated files. The wrapper decompresses the archived JSON in its own
working directory; no manual changes to the published inputs are required.

`papers.csv` has one included paper per row. Label cells contain JSON arrays;
blank cells denote invalid/missing fields. `inputs/paper_index.csv` also contains
excluded and unresolved candidates. No source PDFs or model reasoning are bundled.
