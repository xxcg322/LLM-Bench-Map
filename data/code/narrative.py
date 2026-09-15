"""Generate public analysis notes from the same tables used for the figures."""

METHODS = '''# Analysis methods

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
'''

CAPTIONS = '''# Figure and table guide

- Figure 1: selection flow, January 2022-August 2026. Counts are paper records,
  not benchmark families. Undetermined outcomes are not definite exclusions.
- Figure 2: target systems and domains, January-August 2024, 2025 and 2026.
  Multi-label categories overlap; exact numerators and valid denominators are in
  the corresponding figure CSV.
- Figure 3: material origins, evaluation setup and modalities for the same window.
  Program/simulation and generative-model materials are separate categories.
  Fixed task collections can support interactive evaluation.
- Figure 4: scoring-label shares, within-group LLM scoring, and the symmetric
  composition/within-group allocation of the 2024-2026 change. Panel C is in
  percentage points and does not represent causal effects.
- Figure 5: generation-scoring co-occurrence by matched year (A); additional
  material sources and scoring mechanisms among the full-window intersection (B).
  Panel B uses a different conditional denominator, and its categories overlap.

`tables/label_rates.csv` covers every observed label; `field_quality.csv` reports
missing and special states. `language_summary.csv` and `scoring_by_group.csv`
provide system/domain slices. `months.csv` uses first-submission month, not
conference timing or adoption. All figures have adjacent numerical source CSVs.
'''

README = '''# Analysis outputs

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
'''


def make(out, tables, design, roles, flow, cfg):
    from run import csvwrite
    labels, quality, language, strata = tables

    def label(year, field, tag):
        return next(r for r in labels if r['window']=='jan_aug' and r['year']==year
                    and r['field']==field and r['label']==tag)

    def fmt(row):
        return f"{row['n']:,}/{row['valid_n']:,} ({row['share']*100:.1f}%)"

    a, b = [label(y, 'scoring_source', 'llm_judge') for y in ('2024', '2026')]
    dec = next(d for d in design['decompositions'] if d['cohort']=='primary'
               and d['outcome']=='llm' and d['strata']==['agent'] and d['start']=='2024')
    assoc = [next(d for d in design['material_judge_associations']
                  if d['cohort']=='primary' and d['year']==y) for y in ('2024','2026')]
    both, mix = roles['generated_and_llm_judge_n'], roles['within_llm_intersection']
    en = [next(r for r in language if r['window']=='jan_aug' and r['year']==y
               and r['group']=='all' and r['metric']=='en_only') for y in ('2024','2026')]
    claims = [
        dict(id='C01', rq='scope', status='supported_descriptive',
             statement='The analysis includes 14,767 paper records, not 14,767 independent benchmark families.',
             evidence='papers.csv; flow.json', selector='included + included_partial_labels',
             caveat='Selection error and family duplication are not fully quantified; counts do not measure adoption.'),
        dict(id='C02', rq='RQ3', status='supported_descriptive',
             statement=f'LLM scoring rises from {fmt(a)} to {fmt(b)} in the matched January-August windows.',
             evidence='tables/label_rates.csv; figures/fig4_scoring_data.csv',
             selector='jan_aug; 2024/2026; scoring_source=llm_judge',
             caveat='These are coded design shares, not changes in scoring reliability.'),
        dict(id='C03', rq='RQ3', status='supported_arithmetic_not_causal',
             statement=f"Of the {dec['delta']*100:.2f} percentage-point increase, agent composition contributes {dec['composition']*100:.2f} and within-group change {dec['within']*100:.2f}.",
             evidence='design_analysis.json; tables/decompositions.csv',
             selector='primary; outcome=llm; strata=[agent]; start=2024; end=2026',
             caveat='A symmetric arithmetic allocation under this grouping, not a causal effect.'),
        dict(id='C04', rq='RQ2xRQ3', status='supported_descriptive',
             statement=f"Across the full window, {both:,}/{roles['valid_n']:,} ({roles['generated_and_llm_judge_share']*100:.1f}%) combine generated materials with LLM scoring.",
             evidence='roles.json; figures/fig5_material_scoring_data.csv',
             selector='generated_and_llm_judge_n / valid_n',
             caveat='Different roles can involve different models, components or evaluation stages.'),
        dict(id='C05', rq='RQ2xRQ3', status='supported_descriptive',
             statement=f"Within this intersection, {mix['human_material_n']:,}/{both:,} ({mix['human_material_n']/both*100:.1f}%) also use human/real-world materials and {mix['any_additional_scoring_n']:,}/{both:,} ({mix['any_additional_scoring_n']/both*100:.1f}%) additional scoring mechanisms.",
             evidence='roles.json; figures/fig5_material_scoring_data.csv',
             selector=f'within_llm_intersection; conditional denominator={both}',
             caveat='These categories overlap; mixed design does not establish oversight or quality.'),
        dict(id='C06', rq='RQ2xRQ3', status='stronger_interpretation_not_supported',
             statement=f"Joint prevalence increases, but lift changes from {assoc[0]['lift']:.2f} to {assoc[1]['lift']:.2f}; an increasingly strong association is not established.",
             evidence='tables/associations.csv; design_analysis.json',
             selector='primary; 2024/2026; lift and joint_changes',
             caveat='Association strength is distinct from changes in the two marginal shares.'),
        dict(id='C07', rq='RQ2', status='secondary_with_sensitivity',
             statement=f'English-only coding changes from {fmt(en[0])} to {fmt(en[1])}.',
             evidence='tables/language_summary.csv; design_analysis.json',
             selector='jan_aug; all groups; en_only; 2024/2026',
             caveat='Language coverage is a secondary result; absent tags do not prove unsupported languages.'),
    ]
    csvwrite(out/'claim_ledger.csv', claims)
    notes = '# Results guide\n\nThese findings describe the identified literature.\n\n'
    for c in claims:
        notes += (f"## {c['id']} - {c['rq']}\n\n{c['statement']}\n\n"
                  f"Data: `{c['evidence']}`. Selector: `{c['selector']}`.\n\n{c['caveat']}\n\n")
    body = '# Field overview\n\nCounts are paper records; shares use field-valid denominators.\n\n'
    body += '## Full window: January 2022-August 2026\n\n| Field | Valid/included | Missing | Special state | Other |\n| --- | ---: | ---: | ---: | ---: |\n'
    for r in quality:
        if r['window']=='observed' and r['year']=='all':
            body += f"| {r['field']} | {r['valid_n']}/{r['included_n']} | {r['missing_n']} | {r['sentinel_present_n']} | {r['other_n']} |\n"
    for field in cfg['fields']:
        if field=='task_language':
            continue
        body += f'\n## {field}: January-August\n\n| Label | 2024 n/N (%) | 2025 n/N (%) | 2026 n/N (%) |\n| --- | ---: | ---: | ---: |\n'
        for tag in sorted({r['label'] for r in labels if r['field']==field}):
            body += '| '+tag+' | '+' | '.join(fmt(label(y,field,tag)) for y in ('2024','2025','2026'))+' |\n'
    body += '\nAll language codes are in `tables/label_rates.csv`; language slices are in `tables/language_summary.csv`. Multi-label percentages may sum to more than 100%.\n'
    for name, text in {'METHODS.md':METHODS, 'CAPTIONS.md':CAPTIONS, 'README.md':README,
                       'RESULTS_NOTES.md':notes, 'OVERVIEW.md':body}.items():
        (out/name).write_text(text, encoding='utf-8')
