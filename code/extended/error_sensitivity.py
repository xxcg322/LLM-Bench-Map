"""Offline, bounded-error scenarios. Not an accuracy estimator."""
import csv
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'diagnostics'
DATA = ROOT / 'data'
OUT = ROOT / 'reproduced_error_sensitivity'
sys.path.insert(0, str(ROOT))
from integrity import digest, verify_release
SOURCES = []


def source(path):
    path = Path(path)
    raw = path.read_bytes()
    SOURCES.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': digest(path)})
    return raw.decode('utf-8-sig')


def read_json(path):
    return json.loads(source(path))


def flip_bounds(k, n, budget):
    b = int(budget * n)
    return max(0, k-b)/n, min(n, k+b)/n


def removal_bounds(k, n, budget):
    b = int(budget * n)
    assert b < n
    # Worst case under AT MOST b removals; not replacements/additions.
    return max(0, k-b)/(n-b), min(k, n-b)/(n-b)


def checks():
    assert flip_bounds(3, 10, Fraction(1, 10)) == (.2, .4)
    assert flip_bounds(0, 10, Fraction(1, 10)) == (0, .1)
    assert removal_bounds(3, 10, Fraction(1, 10)) == (2/9, 3/9)
    # Independently enumerate all feasible error/deletion counts on tiny populations.
    for n in range(2, 15):
        for k in range(n+1):
            for b in range(n):
                budget = Fraction(b, n)
                possible = [(k-p+q)/n for p in range(k+1) for q in range(n-k+1) if p+q <= b]
                assert flip_bounds(k, n, budget) == (min(possible), max(possible))
                possible = [(k-p)/(n-p-q) for p in range(k+1) for q in range(n-k+1) if p+q <= b]
                assert removal_bounds(k, n, budget) == (min(possible), max(possible))


def main():
    if not __debug__:
        raise SystemExit('Run without -O so numerical checks remain enabled.')
    verify_release(ROOT)
    SOURCES.clear()
    checks()
    if OUT.exists():
        raise SystemExit('Refusing to overwrite existing result directory')
    rows = list(csv.DictReader(source(DATA / 'papers.csv').splitlines()))
    assert len(rows) == len({r['document_id'] for r in rows}) == 14767
    fields = ['target_system','evaluation_domain','evaluation_setup','material_origin','scoring_source','task_language']
    for r in rows:
        for f in fields:
            r[f] = json.loads(r[f]) if r[f] else None
    published = list(csv.DictReader(source(DATA / 'tables/label_rates.csv').splitlines()))
    measures = [('agent','target_system','agent_or_tool_system'), ('interaction','evaluation_setup','interactive_loop'),
                ('fixed','evaluation_setup','fixed_items'), ('generated_material','material_origin','generative_model'),
                ('llm_judge','scoring_source','llm_judge'), ('execution_score','scoring_source','execution_or_environment'),
                ('english_only','task_language',None)]
    measures += [('domain:'+lab,'evaluation_domain',lab) for lab in sorted({x for r in rows for x in (r['evaluation_domain'] or [])})]
    counts = {}
    verified_rates = 0
    for name, field, label in measures:
        counts[name] = {}
        for year in [2024, 2026]:
            rr = [r for r in rows if r['first_submission_month'][:4] == str(year)
                  and int(r['first_submission_month'][5:7]) <= 8 and r[field] is not None]
            n = len(rr)
            k = sum(r[field] == ['en'] if label is None else label in r[field] for r in rr)
            counts[name][year] = (k,n)
            if label is not None:
                prior = [p for p in published if (p['window'],p['year'],p['field'],p['label']) == ('jan_aug',str(year),field,label)]
                assert len(prior) == 1 and (int(prior[0]['n']),int(prior[0]['valid_n'])) == (k,n)
                verified_rates += 1
    assert counts['english_only'] == {2024:(1332,1677),2026:(4723,5728)}
    scenarios = []
    for name, cc in counts.items():
        k0,n0 = cc[2024]; k1,n1 = cc[2026]
        delta = k1/n1-k0/n0
        for mode, fn in [('label_flips',flip_bounds),('ineligible_removal',removal_bounds)]:
            for percent in [0,1,3,5,10]:
                lo0,hi0 = fn(k0,n0,Fraction(percent,100)); lo1,hi1 = fn(k1,n1,Fraction(percent,100))
                scenarios.append(dict(measure=name,mode=mode,budget_pct_each_year=percent,k2024=k0,n2024=n0,k2026=k1,n2026=n1,
                    observed_delta_pp=100*delta,lower_delta_pp=100*(lo1-hi0),upper_delta_pp=100*(hi1-lo0),
                    sign_preserved=(lo1-hi0>0 if delta>0 else hi1-lo0<0)))
    byid = {r['document_id']:r for r in rows}
    reviews = []
    for part in [1,2]:
        for r in read_json(BASE / f'interaction/targeted_notes_part{part}.json')['checks']:
            final = byid.get(r['document_id'])
            reviews.append(dict(document_id=r['document_id'],kind='exposed_loop_check',prior_finding=r['finding'],prior_note=r['note'],
                final_included=final is not None,final_labels=final['evaluation_setup'] if final else None,
                historical_loop_expectation_met=(('interactive_loop' in final['evaluation_setup']) == (r['finding']=='confirmed_interactive_loop_omission')) if final and final['evaluation_setup'] else None))
    lang = read_json(BASE / 'language/source_review.json')
    for r in lang:
        if not r['preselected']:
            continue
        final = byid.get(r['document_id'])
        reviews.append(dict(document_id=r['document_id'],kind='exposed_language_check',title=r['title'],
            prior_finding=r.get('language_finding'),prior_note=r.get('language_note'),prior_labels=r.get('task_language'),
            final_included=final is not None,final_labels=final['task_language'] if final else None,
            unchanged_vs_reviewed_labels=(sorted(final['task_language']) == sorted(r['task_language'])) if final and final['task_language'] and r.get('task_language') else None))
    OUT.mkdir()
    with (OUT/'scenarios.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(scenarios[0]));writer.writeheader();writer.writerows(scenarios)
    (OUT/'prior_review_comparison.json').write_text(json.dumps(reviews,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUT/'checks.json').write_text(json.dumps(dict(n_papers=len(rows),published_rates_matched=verified_rates,
        scenario_rows=len(scenarios),exhaustive_small_population_bounds='passed',new_model_calls=0,new_source_reviews=0,
        estimates_accuracy=False,source_hashes=SOURCES),indent=2)+'\n',encoding='utf-8')
    for s in scenarios:
        if s['mode']=='label_flips' and s['budget_pct_each_year']==5 and not s['measure'].startswith('domain:'):
            print(s['measure'],round(s['observed_delta_pp'],2),round(s['lower_delta_pp'],2),round(s['upper_delta_pp'],2))
    print('Selected development comparisons',len(reviews),'; rate checks',verified_rates)


if __name__ == '__main__':
    main()
