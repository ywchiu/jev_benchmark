"""Build the decision board for one system from its repeat directories.

Reads predictions.jsonl (canonical dicts) rather than raw responses, so it works for
every adapter uniformly. Scores route / mode / scope_action / boundary + decision_joint,
and folds in latency, failures and token usage from the timing + usage sidecars.
"""
import json,glob,pathlib,sys,collections,statistics as st
sys.path.insert(0,'/Users/david/tests/jev_testing/runs')
from score_decision import gold_map,score_repeat,FIELDS

def pct(v,p):
    v=sorted(v)
    if not v: return None
    return v[min(len(v)-1,max(0,int(round(p/100*len(v)))-1))]

def build(name, gold_path, root):
    gold=gold_map(gold_path)
    root=pathlib.Path(root)
    reps=sorted([d for d in root.glob('rep*') if d.is_dir()],key=lambda p:int(p.name[3:]))
    if not reps: return None
    scores=[]; lat=[]; fail_lat=[]; errs=collections.Counter(); cold=[]; itok=[]; otok=[]; n_att=0
    for d in reps:
        preds={}
        for line in (d/'predictions.jsonl').read_text().splitlines():
            if not line.strip(): continue
            p=json.loads(line)
            if isinstance(p,dict) and 'route' in p:
                preds[p['id']]={'route':p['route'],'mode':p['mode'],
                                'scope_action':p['scope_action'],
                                'boundary':p['scope_after']['boundary']}
        scores.append(score_repeat(preds,gold))
        t=json.loads((d/'predictions.timing.json').read_text())
        recs=t['records']; n_att+=len(recs)
        if recs: cold.append(recs[0]['latency_ms'])
        for x in recs:
            (fail_lat if x['error'] else lat).append(x['latency_ms'])
            if x['error']: errs[x['error']]+=1
        uf=d/'raw'/'_usage.jsonl'
        if uf.exists():
            for line in uf.read_text().splitlines():
                if not line.strip(): continue
                u=json.loads(line); us=u.get('usage') or {}
                i=us.get('input_tokens') or us.get('prompt_tokens') or 0
                o=us.get('output_tokens') or us.get('completion_tokens') or 0
                if i: itok.append(i)
                if o: otok.append(o)
    keys=[f+'_accuracy' for f in FIELDS]+[f+'_macro_f1' for f in FIELDS]+\
         ['decision_joint_accuracy','session_all_decisions_correct_rate','mean_correct_prefix']
    out={'system':name,'gold':gold_path,'repeats':len(reps),'turns_per_repeat':scores[0]['n'],
         'total_attempts':n_att}
    for k in keys:
        v=[s[k] for s in scores]
        out[k]={'mean':round(st.mean(v),4),'min':round(min(v),4),'max':round(max(v),4),
                'per_repeat':v}
    allv=lat+fail_lat
    out['latency_ms']={'p50_all_attempts':round(pct(allv,50),1),'p95_all_attempts':round(pct(allv,95),1),
                       'max':round(max(allv),1),'p50_success_only':round(pct(lat,50),1) if lat else None,
                       'n_success':len(lat),'n_failed':len(fail_lat),
                       'failed_attempt_ms':[round(x,1) for x in fail_lat][:10]}
    out['failures']={'errors':dict(errs),'failure_rate':round(sum(errs.values())/n_att,4)}
    out['cold_start_ms_per_repeat']=[round(x,1) for x in cold]
    if itok: out['input_tokens_per_turn']={'p50':pct(itok,50),'total':sum(itok)}
    if otok: out['output_tokens_per_turn']={'p50':pct(otok,50),'total':sum(otok)}
    # merged confusion matrix for scope_action across repeats
    cm=collections.defaultdict(collections.Counter)
    for s in scores:
        for g,row in s['_cm']['scope_action'].items():
            for p,c in row.items(): cm[g][p]+=c
    out['scope_action_confusion_all_repeats']={k:dict(v) for k,v in cm.items()}
    cmr=collections.defaultdict(collections.Counter)
    for s in scores:
        for g,row in s['_cm']['route'].items():
            for p,c in row.items(): cmr[g][p]+=c
    out['route_confusion_all_repeats']={k:dict(v) for k,v in cmr.items()}
    (root/'decision_board.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    return out

if __name__=='__main__':
    r=build(sys.argv[1],sys.argv[2],sys.argv[3])
    print(json.dumps({k:v for k,v in r.items() if not k.endswith('confusion_all_repeats')},
                     ensure_ascii=False,indent=2))
