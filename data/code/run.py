"""Offline, fail-closed, paper-level analysis. No network or model calls."""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import shutil
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from integrity import digest as content_digest
SENTINELS = {'unclear', 'not_reported', 'not_applicable', 'multilingual_unspecified'}


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def write(p, value):
    Path(p).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def digest(p):
    return content_digest(p)


def csvwrite(p, rows):
    assert rows, str(p)
    keys = list(rows[0])
    with Path(p).open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False, sort_keys=True) if isinstance(v, (list, dict)) else v for k, v in r.items()})


def rate(n, d):
    return n / d if d else None


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def equal(a, b, path='root'):
    if isinstance(a, dict):
        assert set(a) == set(b), path
        for k in a:
            equal(a[k], b[k], path + '.' + k)
    elif isinstance(a, list):
        assert len(a) == len(b), path
        for i, (x, y) in enumerate(zip(a, b)):
            equal(x, y, path + f'[{i}]')
    elif isinstance(a, float):
        assert b is not None and abs(a - b) < 1e-11, (path, a, b)
    else:
        assert a == b, (path, a, b)


def field_counts(rows, field, label):
    valid = [r for r in rows if r['tags'][field] is not None]
    # Sentinel categories remain visible; no inference of true feature absence.
    known = [r for r in valid if not set(r['tags'][field]) & SENTINELS]
    n = sum(label in r['tags'][field] for r in valid)
    kn = sum(label in r['tags'][field] for r in known)
    return dict(n=n, valid_n=len(valid), missing_n=len(rows)-len(valid), included_n=len(rows),
                share=rate(n, len(valid)), sentinel_present_n=len(valid)-len(known),
                known_n=len(known), known_positive_n=kn, known_share=rate(kn, len(known)))


def select(rows, window, year):
    return [r for r in rows if (year == 'all' or r['year'] == year) and
            (window == 'observed' or int(r['month'][5:7]) <= 8)]


def prepare(paths, cfg):
    raw = read(paths['results'])
    with paths['paper_index'].open(encoding='utf-8-sig', newline='') as f:
        idxrows = list(csv.DictReader(f))
    idx = {r['document_id']: r for r in idxrows}
    assert len(idx) == len(idxrows) == len(raw) == 16376
    assert set(idx) == {r['document_id'] for r in raw}
    assert len({r['document_id'].rsplit('v', 1)[0] for r in raw}) == len(raw), 'Multiple versions of one paper'
    versions = read(paths['versions'])['rows']
    rows = []
    for r in raw:
        if r['decision'] not in cfg['included_decisions']:
            continue
        did = r['document_id']
        m = idx[did]['first_submission_month']
        assert cfg['start_month'] <= m <= cfg['end_month']
        assert versions[did]['first_submitted_at'][:7] == m
        tags = {f: sorted(r['analysis_tags'][f]) if r['field_status'][f]['status'] == 'valid' else None for f in cfg['fields']}
        for f, values in tags.items():
            assert values is None or (values and len(values) == len(set(values)))
            assert values == (sorted(json.loads(idx[did][f])) if json.loads(idx[did][f]) is not None else None), (did, f)
        rows.append(dict(id=did, decision=r['decision'], month=m, year=m[:4], tags=tags, **versions[did]))
    assert len(rows) == len(versions) == 14767
    return sorted(rows, key=lambda x: x['id']), idx, raw


def recompute_design(rows, module, prior):
    recs = []
    for r in rows:
        v = dict(r)
        for key, (field, tag) in module.SPECS.items():
            v[key] = tag in r['tags'][field] if r['tags'][field] is not None else None
        lang = set(r['tags']['task_language']) if r['tags']['task_language'] is not None else None
        v['en_only'] = lang == {'en'} if lang is not None else None
        v['en_only_named'] = v['en_only'] if lang and not lang & module.SENTINELS else None
        v['multiple_named'] = len(lang-module.SENTINELS) >= 2 if lang is not None else None
        recs.append(v)
    primary = [r for r in recs if r['year'] in ['2024', '2025', '2026'] and int(r['month'][5:7]) <= 8]
    cohorts = {'primary': primary,
               'same_year_version': [r for r in primary if r['version_submitted_at'][:4] == r['year']],
               'read_version_year': [{**r, 'year': r['version_submitted_at'][:4]} for r in recs
                                    if r['version_submitted_at'][:4] in ['2024','2025','2026'] and int(r['version_submitted_at'][5:7]) <= 8]}
    ans = {}
    ans['rates'] = [{**{k: t[k] for k in ['cohort','year','metric']},
                     'included_n': len(g), **module.rate(g, t['metric'])}
                    for t in prior['rates'] for g in [[r for r in cohorts[t['cohort']] if r['year'] == t['year']]]]
    ans['decompositions'] = [{'cohort': t['cohort'], **module.decomposition(cohorts[t['cohort']], t['outcome'], t['strata'], t['start'], t['end'])} for t in prior['decompositions']]
    ans['material_judge_associations'] = [{'cohort': t['cohort'], 'year': t['year'], **module.association([r for r in cohorts[t['cohort']] if r['year'] == t['year']])} for t in prior['material_judge_associations']]
    ans['standardized_material_judge'] = [{'cohort': t['cohort'], **module.standardized(cohorts[t['cohort']])} for t in prior['standardized_material_judge']]
    ans['combinations'] = [{'cohort':t['cohort'], 'year':t['year'], **module.combinations([r for r in cohorts[t['cohort']] if r['year']==t['year']], t['fields'])} for t in prior['combinations']]
    ans['domain_slices'] = []
    for t in prior['domain_slices']:
        g = [r for r in cohorts[t['cohort']] if t['domain'] in r['tags']['evaluation_domain'] and (t['year']=='all' or r['year']==t['year'])]
        ans['domain_slices'].append({**{k:t[k] for k in ['cohort','domain','year']}, **module.association(g),
                                   'agent_language':module.association(g,'agent','en_only'),
                                   'agent_n':module.rate(g,'agent'), 'interactive_n':module.rate(g,'interactive')})
    ans['joint_changes'] = []
    for t in prior['joint_changes']:
        a,b = [next(x for x in ans['material_judge_associations'] if x['cohort']==t['cohort'] and x['year']==y) for y in [t['start'],t['end']]]
        delta = b['joint_share']-a['joint_share']
        margin = b['independence_product']-a['independence_product']
        ans['joint_changes'].append({**{k:t[k] for k in ['cohort','start','end']}, 'joint_change':delta,
                                     'marginal_product_change':margin, 'excess_change':b['excess_joint_share']-a['excess_joint_share'],
                                     'marginal_fraction_of_joint_change':rate(margin,delta)})
    for key, value in ans.items():
        equal(value, prior[key], key)
    return ans, recs


def build_tables(rows, cfg, summary, out):
    tables = out/'tables'
    tables.mkdir()
    vocabulary = {f: sorted(summary['field_distributions'][f]['tags']) for f in cfg['fields']}
    annual, quality, language, strata = [], [], [], []
    for window in ['observed','jan_aug']:
        for year in ['all'] + cfg['years']:
            group = select(rows, window, year)
            for f in cfg['fields']:
                for tag in vocabulary[f]:
                    annual.append(dict(window=window, year=year, field=f, label=tag, **field_counts(group, f, tag)))
                valid = [r for r in group if r['tags'][f] is not None]
                quality.append(dict(window=window, year=year, field=f, included_n=len(group), valid_n=len(valid), missing_n=len(group)-len(valid),
                                    sentinel_present_n=sum(bool(set(r['tags'][f])&SENTINELS) for r in valid),
                                    other_n=sum('other' in r['tags'][f] for r in valid)))
            groups = [('all', group)] + [(name,[r for r in group if ('agent_or_tool_system' in r['tags']['target_system'])==flag]) for name,flag in [('agent',True),('non_agent',False)]]
            groups += [('domain:'+tag,[r for r in group if tag in r['tags']['evaluation_domain']]) for tag in vocabulary['evaluation_domain']]
            for name, g in groups:
                for tag in vocabulary['scoring_source']:
                    strata.append(dict(window=window, year=year, group=name, field='scoring_source', label=tag,
                                       **field_counts(g,'scoring_source',tag), sparse=len(g)<cfg['minimum_display_n']))
                valid = [r for r in g if r['tags']['task_language'] is not None]
                known = [r for r in valid if not set(r['tags']['task_language']) & SENTINELS]
                for metric, pred in {
                    'en_only': lambda t:t=={'en'}, 'en_any':lambda t:'en' in t,
                    'named_non_en':lambda t:bool(t-SENTINELS-{'en'}),
                    'multiple_named':lambda t:len(t-SENTINELS)>=2,
                    'sentinel_present':lambda t:bool(t&SENTINELS)
                }.items():
                    n = sum(pred(set(r['tags']['task_language'])) for r in valid)
                    kn = sum(pred(set(r['tags']['task_language'])) for r in known)
                    language.append(dict(window=window,year=year,group=name,metric=metric,n=n,valid_n=len(valid),included_n=len(g),
                                         missing_n=len(g)-len(valid),share=rate(n,len(valid)),known_n=len(known),known_positive_n=kn,
                                         known_share=rate(kn,len(known)),sparse=len(valid)<cfg['minimum_display_n']))
    for name, data in [('label_rates',annual),('field_quality',quality),('language_summary',language),('scoring_by_group',strata)]:
        csvwrite(tables/(name+'.csv'),data)
    for f in cfg['fields']:
        g = summary['field_distributions'][f]
        actual = [r for r in annual if r['window']=='observed' and r['year']=='all' and r['field']==f]
        assert all(r['n']==g['tags'][r['label']] and r['valid_n']==g['valid_n'] and r['missing_n']==g['missing_n'] for r in actual)
    return annual, quality, language, strata


def main():
    if not __debug__:
        raise SystemExit('Run without -O so numerical checks remain enabled.')
    ap=argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, required=True, help='A new directory; existing output is never overwritten')
    ap.add_argument('--input-dir',type=Path,help='Frozen inputs/ directory of a previously built bundle')
    args=ap.parse_args()
    out=args.output.resolve()
    assert not out.exists(), f'Refusing overwrite: {out}'
    cfg=read(HERE/'contract.json')
    paths={k: (args.input_dir/(k+Path(v['path']).suffix) if args.input_dir else ROOT/v['path']).resolve() for k,v in cfg['sources'].items()}
    for k,p in paths.items():
        assert digest(p)==cfg['sources'][k]['sha256'], f'Input hash changed: {k}'
    rows,idx,raw=prepare(paths,cfg)
    summary=read(paths['summary'])
    out.mkdir(parents=True)
    (out/'inputs').mkdir()
    for k,p in paths.items():
        shutil.copyfile(p,out/'inputs'/(k+p.suffix))
    (out/'code').mkdir()
    for p in HERE.iterdir():
        if p.is_file(): shutil.copyfile(p,out/'code'/p.name)
    print('Inputs verified; unique included records:',len(rows),flush=True)
    csvwrite(out/'papers.csv',[dict(document_id=r['id'],decision=r['decision'],first_submission_month=r['month'],
                                  first_submitted_at=r['first_submitted_at'],version_submitted_at=r['version_submitted_at'],
                                  **{f:r['tags'][f] for f in cfg['fields']}) for r in rows])
    tables=build_tables(rows,cfg,summary,out)
    module=load_module('frozen_design',paths['design_code'])
    design,recs=recompute_design(rows,module,read(paths['design_reference']))
    write(out/'design_analysis.json',design)
    rolemodule=load_module('frozen_roles',paths['roles_code'])
    roledata=rolemodule.role_counts([{'material':set(r['tags']['material_origin']) if r['tags']['material_origin'] is not None else None,
                                     'score':set(r['tags']['scoring_source']) if r['tags']['scoring_source'] is not None else None} for r in rows])
    # Pattern ordering is irrelevant; compare counts and scalars independently.
    previous=read(paths['roles_reference'])
    reference=previous['role_counts']
    if isinstance(reference,list): reference=next(x for x in reference if x['window']=='full_observed' and x['year']=='all')
    reference={k:reference[k] for k in roledata}
    for obj in [roledata,reference]:
        for key in ['material_patterns','scoring_patterns']:
            obj['within_llm_intersection'][key].sort(key=lambda x:tuple(x['tags']))
    equal(roledata,reference)
    write(out/'roles.json',roledata)
    monthly=[]
    for m in previous['month_table']:
        counts=Counter(r['decision'] for r in raw if idx[r['document_id']]['first_submission_month']==m['month'])
        assert dict(counts)==m['decision_counts']
        assert counts['included']+counts['included_partial_labels']==m['included_n']
        monthly.append({k:v for k,v in m.items() if not isinstance(v,dict)})
    csvwrite(out/'tables/months.csv',monthly)
    csvwrite(out/'tables/design_rates.csv',design['rates'])
    csvwrite(out/'tables/decompositions.csv',[{k:v for k,v in t.items() if k!='cells'} for t in design['decompositions']])
    csvwrite(out/'tables/associations.csv',design['material_judge_associations'])
    csvwrite(out/'tables/domain_slices.csv',design['domain_slices'])
    flow=dict(frame_n=sum(m['frame_n'] for m in monthly),m0_n=sum(m['m0_retained_n'] for m in monthly),
              **read(paths['collection_summary']),final_decisions=dict(Counter(r['decision'] for r in raw)))
    assert flow['frame_n']==1153355 and flow['m0_n']==173032
    assert sum(flow['metadata_decisions'].values())==flow['m0_n']
    assert flow['source_ready_n']+flow['source_unavailable_n']==flow['candidate_n']
    assert sum(flow['final_decisions'].values())==flow['source_ready_n']
    write(out/'flow.json',flow)
    # Frozen actual source text is not required for arithmetic reproduction.
    import plots
    plots.make(out,tables,design,roledata,flow,cfg)
    import narrative
    narrative.make(out,tables,design,roledata,flow,cfg)
    import verify
    checks=verify.verify(out,paths,cfg)
    write(out/'validation.json',checks)
    write(out/'environment.json',dict(python=platform.python_version(),platform=platform.platform(),
                                     matplotlib=plots.matplotlib.__version__,command=' '.join(sys.argv),
                                     model_calls=0,network_required=False))
    manifest={p.relative_to(out).as_posix():digest(p) for p in sorted(out.rglob('*')) if p.is_file()}
    write(out/'manifest.json',dict(analysis_id=cfg['analysis_id'],files=manifest,calculation_checks_passed=True,
                                  check_scope='Numerical reproduction; does not certify semantic accuracy.'))
    print(json.dumps({'output':str(out),'checks':checks,'files':len(manifest)},ensure_ascii=False),flush=True)


if __name__=='__main__': main()
