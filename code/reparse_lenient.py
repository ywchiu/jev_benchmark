"""Re-score saved raw responses under ONE shared post-processing rule.

Rule (applied identically to every system it is used for):
  1. take message.content
  2. drop a leading non-JSON preamble (e.g. DiffusionGemma's "thought\\n")
  3. strip a ```json ... ``` / ``` ... ``` markdown fence if present
  4. parse the FIRST balanced top-level JSON object found
  5. read answers.<key>.choice for route/mode/scope_action/boundary
Nothing else is repaired: an invalid label, a missing key or unparseable text still fails.
The strict (no post-processing) result is kept separately; this is a labelled experiment,
per the benchmark README's requirement that any post-processing be reported apart from
the unmodified run and shared by all systems it is applied to.
"""
import json, re, sys, glob, pathlib, collections

DECISION_KEYS = ["route", "mode", "scope_action", "boundary"]


def extract_json(text):
    t = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    if m:
        t = m.group(1).strip()
    start = t.find("{")
    if start < 0:
        raise ValueError("no JSON object")
    depth = 0
    in_str = False
    esc = False
    for i, ch in enumerate(t[start:], start):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(t[start:i + 1])
    raise ValueError("unbalanced JSON object")


def normalise_answers(ans):
    """Accept answers as {key: {...}} or as a list of {"id": key, ...}.

    The list form carries an explicit id per element, so converting it is a faithful
    read of the model's own labelling, not a guess. Forms that identify questions only
    by position (e.g. keys "1".."4") are NOT accepted: mapping those would be inventing
    an answer the model did not name.
    """
    if isinstance(ans, list):
        out = {}
        for el in ans:
            if not isinstance(el, dict) or "id" not in el:
                raise ValueError("list-form answer without explicit id")
            out[el["id"]] = el
        return out
    if isinstance(ans, dict):
        return ans
    raise ValueError("answers is neither object nor list")


def parse_raw(raw, criteria):
    content = raw["choices"][0]["message"]["content"]
    obj = extract_json(content)
    ans = normalise_answers(obj["answers"])
    out = {}
    for k in DECISION_KEYS:
        c = ans[k]["choice"] if isinstance(ans[k], dict) else ans[k]
        if c not in criteria[k]:
            raise ValueError("invalid label for %s: %r" % (k, c))
        out[k] = c
    return out


def main(run_dir, tag, out_name):
    sys.path.insert(0, "/Users/david/tests/jev_testing/work/rag-routing-benchmark-v2/multiturn")
    from adapters_ext import _decision_questions
    crit = {k: set(v["criteria"]) for k, v in _decision_questions().items()}
    root = pathlib.Path(run_dir)
    stats = collections.Counter()
    for rep in sorted(root.glob("rep*")):
        preds = []
        for f in sorted(rep.glob("raw/*.%s.json" % tag)):
            cid = f.name.split(".")[0]
            raw = json.loads(f.read_text())
            try:
                lab = parse_raw(raw, crit)
                preds.append({"id": cid, "route": lab["route"], "mode": lab["mode"],
                              "targets": [], "scope_action": lab["scope_action"],
                              "scope_after": {"boundary": lab["boundary"], "focus_targets": []}})
                stats["parsed"] += 1
            except Exception as e:
                preds.append({"id": cid})
                stats["failed_" + type(e).__name__] += 1
        (rep / out_name).write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in preds))
    print(run_dir, dict(stats))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "predictions_lenient.jsonl")
