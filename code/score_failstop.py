"""fail_stop scoring: unreached turns stay in the full gold denominator as incomplete.
evaluate.py's session_all_correct_rate only counts turns that were actually attempted,
which inflates fail_stop; this computes the protocol-correct version."""
import json,pathlib,sys,collections,statistics as st

def load(p): return [json.loads(x) for x in pathlib.Path(p).read_text().splitlines() if x.strip()]

def main(gold_path, root):
    gold=load(gold_path)
    by_sess=collections.defaultdict(list)
    for g in gold: by_sess[g['session_id']].append(g)
    for k in by_sess: by_sess[k].sort(key=lambda r:r['turn_index'])
    root=pathlib.Path(root)
    reps=sorted([d for d in root.glob('rep*') if d.is_dir()],key=lambda p:int(p.name[3:]))
    rows=[]
    for d in reps:
        preds={p['id']:p for p in load(d/'predictions.jsonl') if isinstance(p,dict) and 'id' in p}
        sess_full=0; prefixes=[]; first_err=[]; attempted=0
        for sid,turns in by_sess.items():
            pref=0; err=None
            for g in turns:
                if g['id'] not in preds:   # never reached
                    break
                attempted+=1
                from_eval=sys.modules['evaluate'].equal(g['gold'],preds[g['id']])
                if not from_eval:
                    err=g['turn_index']; break
                pref+=1
            prefixes.append(pref)
            first_err.append(err if err is not None else (None if pref==len(turns) else pref+1))
            if pref==len(turns): sess_full+=1
        rows.append({'repeat':d.name,
                     'sessions':len(by_sess),
                     'full_pass_sessions':sess_full,
                     'full_pass_rate':round(sess_full/len(by_sess),4),
                     'mean_correct_prefix':round(st.mean(prefixes),3),
                     'turns_attempted':attempted,
                     'turns_in_full_gold':len(gold),
                     'turns_unreached':len(gold)-attempted,
                     'first_error_turn_hist':dict(collections.Counter(x for x in first_err if x is not None))})
    out={'gold':gold_path,'run_dir':str(root),'per_repeat':rows,
         'mean_full_pass_rate':round(st.mean([r['full_pass_rate'] for r in rows]),4),
         'mean_correct_prefix':round(st.mean([r['mean_correct_prefix'] for r in rows]),3),
         'mean_turns_unreached':round(st.mean([r['turns_unreached'] for r in rows]),1)}
    print(json.dumps(out,ensure_ascii=False,indent=2))
    (root/'failstop_summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')

sys.path.insert(0,'/Users/david/tests/jev_testing/work/rag-routing-benchmark-v2/multiturn')
import evaluate
main(sys.argv[1], sys.argv[2])
