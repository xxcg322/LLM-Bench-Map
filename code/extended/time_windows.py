"""Full-year and matched-month comparisons of the released paper records."""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'data'
DEFAULT = ROOT / 'reproduced_time_windows'
sys.path.insert(0, str(ROOT))
from integrity import digest, verify_release
FIELDS = ['target_system', 'evaluation_domain', 'evaluation_setup', 'modality',
          'material_origin', 'scoring_source', 'task_language']
SPECIAL = {'unclear', 'not_reported', 'not_applicable', 'multilingual_unspecified'}
WINDOWS = {'full_year': list(range(2022, 2026)), 'jan_aug': list(range(2022, 2027))}
NAMES = {'agent': 'Agent/tool system', 'interactive': 'Interactive evaluation', 'fixed': 'Fixed items',
         'runtime': 'Runtime-generated items', 'generated': 'Model-generated materials',
         'llm': 'LLM scoring', 'reference': 'Reference/metric scoring', 'execution': 'Execution/environment scoring',
         'human_judge': 'Human scoring', 'en_only': 'English-only coding',
         'fixed_and_interactive': 'Fixed and interactive', 'generated_and_llm': 'Generated materials and LLM scoring'}


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    return digest(p)


def csvrows(p):
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def module(p):
    spec = importlib.util.spec_from_file_location('design_functions', p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fraction(n, d):
    return n / d if d else None


def field_rate(rows, field, tag):
    values = [r['tags'][field] for r in rows if r['tags'][field] is not None]
    known = [v for v in values if not set(v) & SPECIAL]
    n, kn = sum(tag in v for v in values), sum(tag in v for v in known)
    return dict(n=n, valid_n=len(values), share=fraction(n, len(values)),
                missing_n=len(rows)-len(values), sentinel_present_n=len(values)-len(known),
                known_n=len(known), known_positive_n=kn, known_share=fraction(kn, len(known)))


def sign(v):
    return 'up' if v > 1e-12 else 'down' if v < -1e-12 else 'flat'


def mdtable(headers, rows):
    return ['| ' + ' | '.join(map(str, headers)) + ' |',
            '| ' + ' | '.join(['---']*len(headers)) + ' |'] + [
            '| ' + ' | '.join(map(str, r)) + ' |' for r in rows]


def percent(v):
    return 'NA' if v is None else f'{100*v:.1f}%'


def main():
    if not __debug__:
        raise SystemExit('Run without -O so numerical checks remain enabled.')
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, default=DEFAULT)
    out = ap.parse_args().output
    assert not out.exists(), 'Use a new output directory; never overwrite completed output.'
    manifest = verify_release(ROOT)
    names = ['papers.csv', 'tables/label_rates.csv', 'tables/language_summary.csv',
             'design_analysis.json', 'inputs/design_code.py']
    source_hashes = {}
    for name in names:
        assert sha(BASE/name) == manifest['files']['data/'+name], name
        source_hashes[name] = sha(BASE/name)
    design = module(BASE/'inputs/design_code.py')
    rows = []
    for r in csvrows(BASE/'papers.csv'):
        tags = {f: json.loads(r[f]) if r[f] else None for f in FIELDS}
        assert r['first_submission_month'] == r['first_submitted_at'][:7]
        assert '2022-01' <= r['first_submission_month'] <= '2026-08'
        rec = dict(id=r['document_id'], year=r['first_submission_month'][:4],
                   month=int(r['first_submission_month'][5:7]), tags=tags)
        for metric, (field, tag) in design.SPECS.items():
            rec[metric] = tag in tags[field] if tags[field] is not None else None
        lang = tags['task_language']
        rec['en_only'] = set(lang) == {'en'} if lang is not None else None
        for key, a, b in [('fixed_and_interactive', 'fixed', 'interactive'),
                          ('generated_and_llm', 'generated', 'llm')]:
            rec[key] = rec[a] and rec[b] if rec[a] is not None and rec[b] is not None else None
        rows.append(rec)
    assert len(rows) == len({r['id'] for r in rows}) == 14767
    assert len({r['id'].rsplit('v', 1)[0] for r in rows}) == len(rows)
    vocabulary = {f: sorted({t for r in rows for t in (r['tags'][f] or [])}) for f in FIELDS}
    old = {(r['window'], r['year'], r['field'], r['label']): r
           for r in csvrows(BASE/'tables/label_rates.csv')}
    langold = {(r['window'], r['year']): r for r in csvrows(BASE/'tables/language_summary.csv')
               if r['group'] == 'all' and r['metric'] == 'en_only'}
    labels, metrics, associations, decomps, cohorts = [], [], [], [], []
    checks_n = 0
    for window, years in WINDOWS.items():
        selected = [r for r in rows if int(r['year']) in years and
                    (window == 'full_year' or r['month'] <= 8)]
        oldwindow = 'observed' if window == 'full_year' else 'jan_aug'
        for year in years:
            group = [r for r in selected if r['year'] == str(year)]
            cohorts.append(dict(window=window, year=year, n=len(group)))
            for f in FIELDS:
                for tag in vocabulary[f]:
                    value = field_rate(group, f, tag)
                    prior = old[oldwindow, str(year), f, tag]
                    for key in ['n', 'valid_n', 'missing_n', 'sentinel_present_n', 'known_n', 'known_positive_n']:
                        assert value[key] == int(prior[key]), (window, year, f, tag, key)
                    checks_n += 1
                    labels.append(dict(window=window, year=year, field=f, label=tag, **value))
            for m in NAMES:
                value = design.rate(group, m)
                if m == 'en_only':
                    prior = langold[oldwindow, str(year)]
                    assert value['n'] == int(prior['n']) and value['valid_n'] == int(prior['valid_n'])
                metrics.append(dict(window=window, year=year, metric=m, **value))
            a = design.association(group)
            assert a['both_n'] + a['neither_n'] + a['exposure_only_n'] + a['outcome_only_n'] == a['valid_n']
            associations.append(dict(window=window, year=year, **a))
        pairs = sorted(set(zip(years[:-1], years[1:])) | {(years[0], years[-1]), (2024, years[-1])})
        for start, end in pairs:
            d = design.decomposition(selected, 'llm', ['agent'], str(start), str(end))
            # Independent weighted-total reconstruction from the actual cell counts.
            for i in [0, 1]:
                assert sum(c['counts'][i] for c in d['cells']) == d['valid_n'][i]
                assert abs(sum(c['positive_n'][i] for c in d['cells']) / d['valid_n'][i] - d['rates'][i]) < 1e-12
            if d['available']:
                assert abs(d['delta'] - d['composition'] - d['within']) < 1e-12
            decomps.append(dict(window=window, any_sparse_group=any(c['sparse_below20'] for c in d['cells']), **d))
    prior = next(d for d in read(BASE/'design_analysis.json')['decompositions']
                 if d['cohort'] == 'primary' and d['outcome'] == 'llm' and d['strata'] == ['agent']
                 and d['start'] == '2024' and d['end'] == '2026')
    current = next(d for d in decomps if d['window'] == 'jan_aug' and d['start'] == '2024' and d['end'] == '2026')
    for key in ['delta', 'composition', 'within']:
        assert abs(current[key] - prior[key]) < 1e-12
    lookup = {(r['window'], r['year'], r['field'], r['label']): r for r in labels}
    comparisons = []
    for f in FIELDS:
        for tag in vocabulary[f]:
            deltas = {w: lookup[w, 2025, f, tag]['share'] - lookup[w, 2022, f, tag]['share'] for w in WINDOWS}
            seq = {w: [lookup[w, y, f, tag]['share'] for y in years] for w, years in WINDOWS.items()}
            comparisons.append(dict(field=f, label=tag, full_year_delta_pp=100*deltas['full_year'],
                                    jan_aug_delta_pp=100*deltas['jan_aug'], same_direction=sign(deltas['full_year']) == sign(deltas['jan_aug']),
                                    yearly_step_directions={w: [sign(b-a) for a,b in zip(v, v[1:])] for w,v in seq.items()}))
    result = dict(cohorts=cohorts, label_rates=labels, key_metrics=metrics, associations=associations,
                  decompositions=decomps, same_endpoint_2022_2025=comparisons)
    out.mkdir(parents=True)
    (out/'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    lines = ['# Full years and matched calendar windows', '',
             'Full years 2022-2025 and January-August 2022-2026.', '',
             '## Scope', '',
             'The unit is an included paper record, grouped by first submission year; labels describe the version read.',
             'Shares use field-valid denominators. Missing fields are not negatives, and labels may coexist.',
             '`analysis.json` retains numerators, denominators, special-state counts and known-only shares.',
             'The windows overlap. Compare the common 2022-2025 endpoints to isolate window choice from adding 2026.', '']
    for window, years in WINDOWS.items():
        title = 'Full years' if window == 'full_year' else 'January-August'
        lines += [f'## {title}', '']
        table = [['Included records'] + [next(r['n'] for r in cohorts if r['window']==window and r['year']==y) for y in years]]
        for m, title_m in NAMES.items():
            table.append([title_m] + [percent(next(r['share'] for r in metrics if r['window']==window and r['year']==y and r['metric']==m)) for y in years])
        lines += mdtable(['Measure']+years, table)+['', 'Denominators can differ by row; see `analysis.json` for exact counts.', '']
        lines += ['### Domains (overlapping)', '']
        lines += mdtable(['Label']+years, [[t]+[percent(lookup[window,y,'evaluation_domain',t]['share']) for y in years] for t in vocabulary['evaluation_domain']])+['']
    lines += ['## Composition and within-group contributions to LLM scoring', '',
              'Units are percentage points. Agent/non-agent partitions are mutually exclusive. Within-group changes compare cohorts, not repeated measurements of identical resources. Groups below 20 records are flagged.', '']
    lines += mdtable(['Window','Years','Total change','Composition','Within-group','Any group below 20'],
                     [[d['window'],f"{d['start']}→{d['end']}",f"{d['delta']*100:.2f}",
                       'NA' if d['composition'] is None else f"{d['composition']*100:.2f}",
                       'NA' if d['within'] is None else f"{d['within']*100:.2f}",d['any_sparse_group']] for d in decomps])+['']
    lines += ['## Generated materials and LLM scoring', '',
              'Lift is joint prevalence divided by the product of marginal shares; it does not establish self-evaluation by the same model.', '']
    lines += mdtable(['Window','Year','Valid records','Intersection','Joint share','Lift'],
                     [[a['window'],a['year'],a['valid_n'],a['both_n'],percent(a['joint_share']),
                       'NA' if a['lift'] is None else f"{a['lift']:.2f}"] for a in associations])+['']
    lines += ['## Checks and interpretation', '',
              'Small early cohorts and later revisions of early papers limit historical interpretation. Similar directions across windows do not remove selection or coding errors.',
              f'All {checks_n} field-count rows match the released aggregate tables; language counts, IDs, dates and decomposition identities also pass.',
              'From the repository root, run `python reproduce.py` to reproduce and compare these results.', '']
    (out/'REPORT.md').write_text('\n'.join(lines), encoding='utf-8')
    checks = dict(unique_papers=14767, field_rows_reconciled=checks_n,
                  language_rows_reconciled=9, prior_2024_2026_decomposition_matched=True,
                  source_hashes_unchanged=all(sha(BASE/n)==h for n,h in source_hashes.items()),
                  semantic_accuracy_measured=False, new_api_calls=0)
    (out/'checks.json').write_text(json.dumps(checks, indent=2)+'\n', encoding='utf-8')
    frozen = dict(input_base=str(BASE.relative_to(ROOT)).replace('\\','/'), inputs=source_hashes,
                  source_manifest_sha256=sha(ROOT/'RELEASE_MANIFEST.json'),
                  code_sha256=sha(Path(__file__)), plan_sha256=sha(Path(__file__).with_name('TIME_WINDOWS_PLAN.md')),
                  outputs={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()})
    (out/'manifest.json').write_text(json.dumps(frozen, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(output=str(out), checks=checks, cohorts=cohorts), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
