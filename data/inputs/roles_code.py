"""Reusable calculations for the released descriptive analyses."""
from collections import Counter

def ratio(a,b):return a/b if b else None


def role_counts(rows):
    valid=[r for r in rows if r['material'] is not None and r['score'] is not None]
    both=[r for r in valid if 'generative_model' in r['material'] and 'llm_judge' in r['score']]
    broad=[r for r in valid if 'generative_model' in r['material'] and r['score']&{'llm_judge','other_model_judge'}]
    material_patterns=Counter(tuple(sorted(r['material'])) for r in both)
    score_patterns=Counter(tuple(sorted(r['score'])) for r in both)
    result={'included_n':len(rows),'valid_n':len(valid),'generated_and_llm_judge_n':len(both),
        'generated_and_llm_judge_share':ratio(len(both),len(valid)),
        'generated_and_any_learned_judge_n':len(broad),'generated_and_any_learned_judge_share':ratio(len(broad),len(valid)),
        'within_llm_intersection':{
            'human_material_n':sum('human_or_real_world' in r['material'] for r in both),
            'human_judge_n':sum('human_judge' in r['score'] for r in both),
            'any_additional_scoring_n':sum(r['score']!={'llm_judge'} for r in both),
            'exact_model_material_and_llm_scoring_n':sum(r['material']=={'generative_model'} and r['score']=={'llm_judge'} for r in both),
            'model_only_material_n':sum(r['material']=={'generative_model'} for r in both),
            'llm_only_scoring_n':sum(r['score']=={'llm_judge'} for r in both),
            'material_patterns':[{'tags':list(k),'n':v} for k,v in material_patterns.most_common()],
            'scoring_patterns':[{'tags':list(k),'n':v} for k,v in score_patterns.most_common()]}}
    assert len(broad)>=len(both) and sum(material_patterns.values())==sum(score_patterns.values())==len(both)
    return result
