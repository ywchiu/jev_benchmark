"""Decision-level scoring: how accurate is the routing/switching DECISION.

The shipped bridge.py joint metric requires all 44 independent Choice answers to be
simultaneously correct, so it is dominated by the 20 target__ + 20 focus__ set-membership
questions and compounds ~20 binary errors into the score. That measures set assembly,
not the decision. Here we score the 4 decision fields directly:
  route        - which channel the request must go to
  scope_action - the switching decision (KEEP/SWITCH/EXPAND/NARROW/ASK/BLOCK)
  mode         - how to process
  boundary     - the source restriction after this turn
plus decision_joint = all four correct.
"""
import json,glob,pathlib,sys,collections,statistics as st

FIELDS=['route','mode','scope_action','boundary']

def gold_map(gold_path):
    g={}
    for l in pathlib.Path(gold_path).read_text().splitlines():
        if not l.strip(): continue
        r=json.loads(l)
        g[r['id']]={'route':r['gold']['route'],'mode':r['gold']['mode'],
                    'scope_action':r['gold']['scope_action'],
                    'boundary':r['gold']['scope_after']['boundary'],
                    'session_id':r['session_id'],'turn_index':r['turn_index']}
    return g

def macro_f1(cm):
    labs=set(cm)|{p for v in cm.values() for p in v}
    fs=[]
    for l in labs:
        tp=cm.get(l,{}).get(l,0)
        fn=sum(cm.get(l,{}).values())-tp
        fp=sum(v.get(l,0) for k,v in cm.items() if k!=l)
        d=2*tp+fp+fn
        if sum(cm.get(l,{}).values()): fs.append(2*tp/d if d else 0.0)
    return sum(fs)/len(fs) if fs else 0.0

def score_repeat(preds, gold):
    """preds: {id: {field: label}}"""
    c=collections.Counter(); cms={f:collections.defaultdict(collections.Counter) for f in FIELDS}
    sess=collections.defaultdict(list); n=0
    for cid,g in gold.items():
        p=preds.get(cid)
        n+=1
        ok_all=True
        for f in FIELDS:
            got=(p or {}).get(f,'__MISSING__')
            good=(got==g[f]); c[f]+=good; ok_all&=good
            cms[f][g[f]][got]+=1
        c['decision_joint']+=ok_all
        sess[g['session_id']].append((g['turn_index'],ok_all))
    out={f+'_accuracy':round(c[f]/n,4) for f in FIELDS}
    out['decision_joint_accuracy']=round(c['decision_joint']/n,4)
    for f in FIELDS: out[f+'_macro_f1']=round(macro_f1({k:dict(v) for k,v in cms[f].items()}),4)
    det={}
    for sid,ts in sess.items():
        ts.sort(); pref=0
        for _,ok in ts:
            if not ok: break
            pref+=1
        det[sid]={'all_correct':all(x[1] for x in ts),'prefix':pref}
    out['session_all_decisions_correct_rate']=round(sum(d['all_correct'] for d in det.values())/len(det),4)
    out['mean_correct_prefix']=round(st.mean([d['prefix'] for d in det.values()]),3)
    out['n']=n
    out['_cm']={f:{k:dict(v) for k,v in cms[f].items()} for f in FIELDS}
    return out
