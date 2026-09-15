# Analysis methods

This is a systematic mapping with descriptive and exploratory analyses of published
LLM evaluation resources. Analyses were developed after inspecting the data; they
are not preregistered confirmatory hypothesis tests.

## Units and denominators

One record represents one exact version of a paper. Benchmark families across papers
are not fully deduplicated. Both complete and partially coded included records enter
the analysis. For each field, share = labelled records / records with valid coding
for that field. Cross-field statistics require all relevant fields to be valid.
Multi-label percentages need not sum to 100%; domain slices overlap.

Missing fields are not negatives. Unclear, unreported and applicable special states
are retained. Additional known-only summaries exclude records containing these
states in the relevant field. An unselected label does not establish absence in the
underlying benchmark. Language tags describe explicit coverage in the paper;
`multilingual_unspecified` may coexist with named languages.

## Time windows

Cohorts use first-submission dates from January 2022 through August 2026; labels
describe the version read. Base figures compare January-August in 2024, 2025 and
2026. Supplementary analyses compare full years 2022-2025 and January-August
2022-2026. The 2026 partial year is not compared as a full year. Early cohorts and
groups below 20 records are retained but not emphasized as trend evidence.
Version-year and same-year-version subsets provide sensitivity checks, not a
reconstruction of original benchmark designs at release.

## Decomposition and association

For group rate r and weight w, the symmetric decomposition is
delta R = sum(delta w * mean r) + sum(delta r * mean w). Agent/non-agent is the
primary mutually exclusive grouping. The terms are arithmetic composition and
within-group contributions, not causal effects or longitudinal changes in the
same resources. Finer groupings are sensitivity checks.

Generation-scoring associations use joint shares, products of marginal shares,
their differences and lift. Paper-level co-occurrence does not establish a shared
model, component or fully automated evaluation loop.

## Checks and interpretation

The code checks unique IDs, joins, date membership, stage totals, field denominators
and decomposition identities. Label and language counts are independently rebuilt
from the candidate CSV and reconciled with the structured coding records. The
release compares regenerated numerical outputs against fixed reference files.

These are computational checks, not estimates of semantic accuracy or recall.
Automated selection and coding may introduce differential errors across cohorts.
The accompanying paper reports its eligibility reviews; no overall seven-field
accuracy estimate is inferred from this package. Hypothetical error-budget scenarios
are conditional bounds, not confidence intervals or measured error rates.
