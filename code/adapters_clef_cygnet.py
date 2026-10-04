"""Adapters for Clef / Clef-flash (Cloudflare) and Cygnet (blockbrain-ai/cygnet-recipe).

All three speak the Jev/SystemOne contract (POST /v1/systemone with model + state + questions), so each
adapter sends the same redesigned 11 questions as jev_redesigned and assembles the answers with the same
_assemble() rules. Raw responses and usage are saved exactly as the other adapters do.

  clef_local_redesigned  self-hosted open weights behind clef_server.py
                         env: CLEF_ENDPOINT (default http://127.0.0.1:18020/v1/systemone), CLEF_MODEL
  clef_api_redesigned    Cloudflare Workers AI hosted endpoint
                         env: CLOUDFLARE_ACCOUNT_ID, CLEF_KEY, CLEF_MODEL (clef | clef-flash)
  cygnet_redesigned      cygnet-recipe shim/decision_server.py in front of a vLLM server
                         env: CYGNET_ENDPOINT (default http://127.0.0.1:8011/v1/systemone)
"""
import os, time
from bridge import state
from adapters_ext import post, save_raw, log_usage, redesigned_questions, _assemble


def _labels(raw, q):
    if "error" in raw:
        raise ValueError(str(raw["error"])[:200] + " / " + str(raw.get("detail", ""))[:200])
    a = raw["answers"]
    if set(a) != set(q):
        raise ValueError("Wrong question IDs")
    labels = {}
    for k in q:
        c = a[k].get("choice")
        if c not in q[k]["criteria"]:
            raise ValueError("Invalid Choice answer: " + k)
        labels[k] = c
    return labels


def _run(row, url, model, tag, key=None, unwrap=False):
    q = redesigned_questions(row)
    payload = {"model": model, "state": state(row), "questions": q}
    t0 = time.perf_counter()
    raw = post(url, payload, key)
    dt = time.perf_counter() - t0
    save_raw(row["id"], raw, tag)
    res = raw.get("result", raw) if unwrap else raw      # Workers AI wraps the body in {"result": ...}
    labels = _labels(res, q)
    log_usage(row["id"], tag, {"wall_ms": 1000 * dt, "server_ms": res.get("timing_ms"),
                               "model": res.get("model"), "usage": res.get("usage"), "n_questions": len(q)})
    return _assemble(row["id"], labels, row)


def clef_local_redesigned(row):
    model = os.environ.get("CLEF_MODEL", "clef")
    return _run(row, os.environ.get("CLEF_ENDPOINT", "http://127.0.0.1:18020/v1/systemone"), model,
                os.environ.get("ROUTING_ADAPTER_TAG", model + "_local"))


def clef_api_redesigned(row):
    model = os.environ.get("CLEF_MODEL", "clef")
    url = ("https://api.cloudflare.com/client/v4/accounts/" + os.environ["CLOUDFLARE_ACCOUNT_ID"]
           + "/ai/run/@cf/cloudflare/" + model)
    return _run(row, url, model, os.environ.get("ROUTING_ADAPTER_TAG", model + "_api"),
                key=os.environ["CLEF_KEY"], unwrap=True)


def cygnet_redesigned(row):
    return _run(row, os.environ.get("CYGNET_ENDPOINT", "http://127.0.0.1:8011/v1/systemone"), "cygnet",
                os.environ.get("ROUTING_ADAPTER_TAG", "cygnet"))
