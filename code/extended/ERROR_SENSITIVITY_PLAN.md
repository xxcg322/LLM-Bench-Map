# Error-sensitivity analysis

This is a post-data sensitivity analysis, not an estimate of actual coding errors.
It compares January-August 2024 with January-August 2026.

For each binary label, assume at most 1%, 3%, 5% or 10% of valid records in each
year are mislabeled. Integer budgets allow worst-case flips in opposite directions
across the two years. A separate scenario removes at most the same percentage of
potentially ineligible records. The two scenarios are not combined into a confidence
interval. They do not cover upstream omissions or incorrect grouping labels.

Bounds are checked by exhaustive enumeration of small populations. Published
counts are reconciled with the base table. Selected development findings are
compared with final records for diagnostic context, without treating them as a
random sample or using them to set the hypothetical error budgets.
