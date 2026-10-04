"""Minimal Jev/SystemOne-compatible HTTP server for Cloudflare Clef open weights (used for clef_redesigned / clef_flash_redesigned).
POST /v1/systemone  (same body as Jev)  ->  {model, answers, usage, timing_ms}
env: CLEF_REPO (Cloudflare/clef-flash | Cloudflare/clef), PORT
"""
import os, sys, time, threading
import torch
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from huggingface_hub import snapshot_download
import uvicorn

REPO = os.environ.get("CLEF_REPO", "Cloudflare/clef-flash")
path = snapshot_download(REPO)
sys.path.insert(0, path)
from joint_schema_model import load_release_model, systemone

t0 = time.time()
model, processor = load_release_model(path, device="cuda")
print(f"loaded {REPO} in {time.time()-t0:.1f}s, mem {torch.cuda.memory_allocated()/2**30:.1f} GiB", flush=True)
lock = threading.Lock()
app = FastAPI()

@app.post("/v1/systemone")
async def run(req: Request):
    body = await req.json()
    try:
        with lock:
            torch.cuda.synchronize(); t = time.perf_counter()
            out = systemone(model, processor, body)
            torch.cuda.synchronize(); out["timing_ms"] = round(1000 * (time.perf_counter() - t), 1)
        out["peak_mem_gib"] = round(torch.cuda.max_memory_allocated() / 2**30, 2)
        return out
    except Exception as e:
        return JSONResponse({"error": type(e).__name__, "detail": str(e)[:500]}, status_code=400)

@app.get("/health")
def health(): return {"ok": True, "repo": REPO}

uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "18020")), log_level="warning")
