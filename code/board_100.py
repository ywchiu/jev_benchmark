"""Score a system over all 100 decision points (dev 20 + test 80) per repeat.

The package splits 20 dev / 80 test by whole session. The dev turns were also used for
wiring, format validation and (for Laya and djev-spark) decoding-config selection, so
they are NOT clean held-out data for every system; that is flagged per system in the
report. This board reports the full 100 anyway, plus the dev/test split, so both
readings are available.
"""
import json, glob, pathlib, sys, collections, statistics as st
sys.path.insert(0, '/Users/david/tests/jev_testing/runs')
from score_decision import gold_map, score_repeat, FIELDS

MT = '/Users/david/tests/jev_testing/work/rag-routing-benchmark-v2/multiturn'


def load_preds(path):
    preds = {}
    for line in pathlib.Path(path).read_text().splitlines():
        if not line.strip():
            continue
        p = json.loads(line)
        if isinstance(p, dict) and 'route' in p:
            preds[p['id']] = {'route': p['route'], 'mode': p['mode'],
                              'scope_action': p['scope_action'],
                              'boundary': p['scope_after']['boundary']}
    return preds


def lat_of(rep_dir):
    f = pathlib.Path(rep_dir) / 'predictions.timing.json'
    if not f.exists():
        return [], 0
    recs = json.loads(f.read_text())['records']
    return [x['latency_ms'] for x in recs], sum(1 for x in recs if x['error'])


def build(name, run_root, dev_sub='dev_teacher_forced', test_sub='test_teacher_forced',
          pred_name='predictions.jsonl'):
    root = pathlib.Path(run_root)
    gold_all = {**gold_map(MT + '/dev_gold.jsonl'), **gold_map(MT + '/test_gold.jsonl')}
    gold_dev = gold_map(MT + '/dev_gold.jsonl')
    gold_test = gold_map(MT + '/test_gold.jsonl')
    devs = sorted((root / dev_sub).glob('rep*'), key=lambda p: int(p.name[3:])) if (root / dev_sub).exists() else []
    tests = sorted((root / test_sub).glob('rep*'), key=lambda p: int(p.name[3:])) if (root / test_sub).exists() else []
    n = min(len(devs), len(tests))
    if n == 0:
        return None
    rows_all, rows_dev, rows_test, lat, fails, total = [], [], [], [], 0, 0
    for i in range(n):
        pd_, pt = load_preds(devs[i] / pred_name), load_preds(tests[i] / pred_name)
        rows_all.append(score_repeat({**pd_, **pt}, gold_all))
        rows_dev.append(score_repeat(pd_, gold_dev))
        rows_test.append(score_repeat(pt, gold_test))
        for d in (devs[i], tests[i]):
            l, f = lat_of(d)
            lat += l; fails += f; total += len(l)
    m = lambda rows, k: st.mean([r[k] for r in rows])
    lat.sort()
    out = {'system': name, 'repeats': n, 'turns_per_repeat': 100,
           'dev_turns': rows_dev[0]['n'], 'test_turns': rows_test[0]['n']}
    for k in [f + '_accuracy' for f in FIELDS] + [f + '_macro_f1' for f in FIELDS] + \
             ['decision_joint_accuracy', 'session_all_decisions_correct_rate', 'mean_correct_prefix']:
        out['all100_' + k] = round(m(rows_all, k), 4)
        out['dev20_' + k] = round(m(rows_dev, k), 4)
        out['test80_' + k] = round(m(rows_test, k), 4)
    out['latency_ms'] = {'p50': round(lat[len(lat) // 2], 1) if lat else None,
                         'p95': round(lat[int(len(lat) * .95) - 1], 1) if lat else None,
                         'n': total}
    out['failures'] = {'n': fails, 'rate': round(fails / total, 4) if total else 0}
    cm = collections.defaultdict(collections.Counter)
    for r in rows_all:
        for g, row in r['_cm']['scope_action'].items():
            for p, c in row.items():
                cm[g][p] += c
    out['scope_action_confusion_100'] = {k: dict(v) for k, v in cm.items()}
    cr = collections.defaultdict(collections.Counter)
    for r in rows_all:
        for g, row in r['_cm']['route'].items():
            for p, c in row.items():
                cr[g][p] += c
    out['route_confusion_100'] = {k: dict(v) for k, v in cr.items()}
    (root / 'board_100.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    return out


if __name__ == '__main__':
    r = build(sys.argv[1], sys.argv[2])
    print(json.dumps({k: v for k, v in r.items() if not k.endswith('_confusion_100')},
                     ensure_ascii=False, indent=2) if r else 'no paired dev+test reps')
