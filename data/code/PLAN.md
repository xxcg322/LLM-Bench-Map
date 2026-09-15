# Base analysis design

Descriptive and exploratory analyses of the already-inspected coded corpus;
not a confirmatory preregistration. One exact-version paper is one record.

The pipeline verifies source hashes, unique IDs and cohort membership, then computes
all field-label counts and valid denominators. It retains invalid fields separately
and produces known-only sensitivity summaries without changing the annotations.

The analysis includes system/domain slices, generation-scoring associations,
symmetric composition/within-group decomposition and version-year sensitivity
checks. It reconciles counts with the candidate CSV through a separate arithmetic
path. Base figures compare January-August in 2024, 2025 and 2026; earlier records
remain in the complete tables. Fewer than 20 records is a display caution, not an
error-control threshold. `METHODS.md` describes interpretation and limitations.
