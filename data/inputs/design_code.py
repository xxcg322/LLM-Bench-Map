"""Reusable calculations for the released descriptive analyses."""
from collections import Counter, defaultdict
import itertools

SENTINELS = {'unclear', 'not_applicable', 'multilingual_unspecified'}


SPECS = {
    'agent': ('target_system', 'agent_or_tool_system'),
    'software': ('evaluation_domain', 'software_and_coding'),
    'interactive': ('evaluation_setup', 'interactive_loop'),
    'fixed': ('evaluation_setup', 'fixed_items'),
    'runtime': ('evaluation_setup', 'runtime_generated_items'),
    'generated': ('material_origin', 'generative_model'),
    'llm': ('scoring_source', 'llm_judge'),
    'reference': ('scoring_source', 'reference_or_metric'),
    'execution': ('scoring_source', 'execution_or_environment'),
    'human_judge': ('scoring_source', 'human_judge'),
    'human_material': ('material_origin', 'human_or_real_world'),
}


def share(n, d):
    return n/d if d else None


def rate(rows, metric):
    values = [r[metric] for r in rows if r[metric] is not None]
    return {'n': sum(values), 'valid_n': len(values), 'share': share(sum(values),len(values))}


def decomposition(rows, outcome, strata, start, end):
    groups = {year: defaultdict(list) for year in [start, end]}
    for r in rows:
        if r['year'] in groups and all(r[x] is not None for x in [outcome]+strata):
            groups[r['year']][tuple(r[x] for x in strata)].append(r[outcome])
    total = {y: sum(map(len, groups[y].values())) for y in groups}
    keys = sorted(set(groups[start])|set(groups[end]))
    cells = []
    for key in keys:
        values = [groups[y][key] for y in [start,end]]
        counts = [len(v) for v in values]
        rates = [share(sum(v),len(v)) for v in values]
        weights = [share(n,total[y]) for n,y in zip(counts,[start,end])]
        available = all(n>0 for n in counts)
        comp = (weights[1]-weights[0])*(rates[1]+rates[0])/2 if available else None
        within = (rates[1]-rates[0])*(weights[1]+weights[0])/2 if available else None
        cells.append({'stratum': dict(zip(strata,key)), 'counts': counts, 'positive_n': [sum(v) for v in values],
                      'rates': rates, 'weights': weights, 'composition': comp, 'within': within, 'sparse_below20': min(counts)<20})
    available = all(c['composition'] is not None for c in cells)
    rs = [sum(sum(v) for v in groups[y].values())/total[y] for y in [start,end]]
    comp = sum(c['composition'] for c in cells) if available else None
    within = sum(c['within'] for c in cells) if available else None
    if available:
        assert abs(comp+within-(rs[1]-rs[0])) < 1e-12
    return {'outcome': outcome, 'strata': strata, 'start': start, 'end': end, 'valid_n': [total[start],total[end]],
            'rates': rs, 'delta': rs[1]-rs[0], 'composition': comp, 'within': within,
            'composition_fraction_of_delta': share(comp,rs[1]-rs[0]) if available else None,
            'available': available, 'cells': cells}


def association(rows, exposure='generated', outcome='llm'):
    counts = Counter((r[exposure],r[outcome]) for r in rows if r[exposure] is not None and r[outcome] is not None)
    n = sum(counts.values())
    a = counts[(True,False)]+counts[(True,True)]
    b = counts[(False,True)]+counts[(True,True)]
    p0 = share(counts[(False,True)], n-a)
    p1 = share(counts[(True,True)], a)
    actual = share(counts[(True,True)],n)
    expected = a*b/n**2 if n else None
    return {'valid_n': n, 'exposure_n': a, 'outcome_n': b, 'both_n': counts[(True,True)],
            'neither_n': counts[(False,False)], 'exposure_only_n': counts[(True,False)], 'outcome_only_n': counts[(False,True)],
            'exposure_share': share(a,n), 'outcome_share': share(b,n), 'p_exposed': p1, 'p_unexposed': p0,
            'risk_difference': p1-p0 if p1 is not None and p0 is not None else None,
            'joint_share': actual, 'independence_product': expected,
            'excess_joint_share': actual-expected if n else None, 'lift': share(actual,expected) if n else None}


def standardized(rows):
    by = defaultdict(list)
    for r in rows:
        if all(r[x] is not None for x in ['generated','llm','agent','software','interactive']):
            by[(r['year'],r['agent'],r['software'],r['interactive'])].append(r)
    cells = []
    for key, group in sorted(by.items()):
        a = association(group)
        keep = a['exposure_n']>=20 and a['valid_n']-a['exposure_n']>=20
        cells.append({'stratum': dict(zip(['year','agent','software','interactive'],key)), **a, 'common_support': keep})
    kept = [c for c in cells if c['common_support']]
    n = sum(c['valid_n'] for c in kept)
    total = sum(c['valid_n'] for c in cells)
    p0 = sum(c['valid_n']*c['p_unexposed'] for c in kept)/n
    p1 = sum(c['valid_n']*c['p_exposed'] for c in kept)/n
    for c in cells:
        c['standard_weight'] = c['valid_n']/n if c['common_support'] else 0
    return {'eligible_n': total, 'retained_n': n, 'retained_share': n/total,
            'p_exposed_standardized': p1, 'p_unexposed_standardized': p0, 'difference': p1-p0, 'cells': cells}


def combinations(rows, fields):
    valid = [r for r in rows if all(r[f] is not None for f in fields)]
    counter = Counter(tuple(r[f] for f in fields) for r in valid)
    return {'valid_n': len(valid), 'fields': fields,
            'cells': [{'combination': dict(zip(fields,key)), 'n': counter[key], 'share':share(counter[key],len(valid))}
                      for key in itertools.product([False,True],repeat=len(fields))]}
