"""Independent reconstruction from the frozen CSV projection, not run.py's records."""
import csv
import json
from collections import Counter


def verify(out,paths,cfg):
    with paths['paper_index'].open(encoding='utf-8-sig',newline='') as f:
        source=list(csv.DictReader(f))
    rows=[]
    for s in source:
        if s['decision'] in cfg['included_decisions']:
            rows.append({'month':s['first_submission_month'],'decision':s['decision'],
                         **{k:json.loads(s[k]) for k in cfg['fields']}})
    tests=Counter()
    sent={'unclear','not_reported','not_applicable','multilingual_unspecified'}
    groups={(w,y):[r for r in rows if (y=='all' or r['month'][:4]==y) and (w=='observed' or int(r['month'][5:7])<=8)]
            for w in ['observed','jan_aug'] for y in ['all']+cfg['years']}
    with (out/'tables/label_rates.csv').open(encoding='utf-8',newline='') as f:
        for line in csv.DictReader(f):
            g=groups[line['window'],line['year']]
            values=[r[line['field']] for r in g if r[line['field']] is not None]
            known=[v for v in values if not set(v)&sent]
            actual={'included_n':len(g),'valid_n':len(values),'missing_n':len(g)-len(values),'n':sum(line['label'] in v for v in values),
                    'known_n':len(known),'known_positive_n':sum(line['label'] in v for v in known),'sentinel_present_n':len(values)-len(known)}
            assert all(int(line[k])==v for k,v in actual.items()),line
            assert not line['share'] if not values else abs(float(line['share'])-actual['n']/len(values))<1e-12
            if known: assert abs(float(line['known_share'])-actual['known_positive_n']/len(known))<1e-12
            tests['independent_label_rows']+=1
    with (out/'tables/language_summary.csv').open(encoding='utf-8',newline='') as f:
        for t in csv.DictReader(f):
            g=groups[t['window'],t['year']]
            if t['group'] in ['agent','non_agent']:g=[r for r in g if ('agent_or_tool_system' in r['target_system'])==(t['group']=='agent')]
            elif t['group'].startswith('domain:'):g=[r for r in g if t['group'][7:] in r['evaluation_domain']]
            v=[set(r['task_language']) for r in g if r['task_language'] is not None]
            rule={'en_only':lambda a:a=={'en'},'en_any':lambda a:'en' in a,'named_non_en':lambda a:len(a-sent-{'en'})>0,
                  'multiple_named':lambda a:len(a-sent)>=2,'sentinel_present':lambda a:len(a&sent)>0}[t['metric']]
            assert (sum(rule(a) for a in v),len(v),len(g))==(int(t['n']),int(t['valid_n']),int(t['included_n']))
            tests['independent_language_rows']+=1
    # Alternate decomposition: average the two sequential paths.
    design=json.loads((out/'design_analysis.json').read_text(encoding='utf-8'))
    for d in design['decompositions']:
        if not d['available']:continue
        w1r0=sum(c['weights'][1]*c['rates'][0] for c in d['cells'])
        w0r1=sum(c['weights'][0]*c['rates'][1] for c in d['cells'])
        r0,r1=d['rates']
        assert abs(((w1r0-r0)+(r1-w0r1))/2-d['composition'])<1e-12
        assert abs(((w0r1-r0)+(r1-w1r0))/2-d['within'])<1e-12
        tests['alternate_decomposition_identities']+=1
    return dict(status='calculation_checks_passed',checks=dict(tests),unique_included=len(rows),
                no_independent_semantic_accuracy_claim=True,
                caveats=['Nonrandom screening and model coding errors are not corrected by arithmetic QA.',
                         'Field-valid label rates include explicitly reported uncertainty; known-only sensitivity is also supplied.',
                         'Paper-level repeated benchmark families have not been comprehensively deduplicated.'])
