"""Render the decision board of every system that has one into a markdown table."""
import json,glob,pathlib,sys
rows=[]
for f in sorted(glob.glob('/Users/david/tests/jev_testing/runs/*/*/decision_board.json')):
    d=json.load(open(f))
    rows.append(d)
if not rows:
    print('no boards yet'); sys.exit()
def g(d,k,f='mean'):
    v=d.get(k)
    return v[f] if isinstance(v,dict) else v
hdr=['系統','repeats','scope_action','scope_action F1','route','route F1','mode','boundary','4欄全對','整段全對','p50 ms','p95 ms','失敗率']
print('| '+' | '.join(hdr)+' |')
print('|'+'---|'*len(hdr))
for d in sorted(rows,key=lambda x:-g(x,'scope_action_accuracy')):
    lat=d['latency_ms']
    print('| {} | {} | {:.1%} | {:.3f} | {:.1%} | {:.3f} | {:.1%} | {:.1%} | {:.1%} | {:.1%} | {:.0f} | {:.0f} | {:.2%} |'.format(
        d['system'], d['repeats'],
        g(d,'scope_action_accuracy'), g(d,'scope_action_macro_f1'),
        g(d,'route_accuracy'), g(d,'route_macro_f1'),
        g(d,'mode_accuracy'), g(d,'boundary_accuracy'),
        g(d,'decision_joint_accuracy'), g(d,'session_all_decisions_correct_rate'),
        lat['p50_all_attempts'], lat['p95_all_attempts'], d['failures']['failure_rate']))
