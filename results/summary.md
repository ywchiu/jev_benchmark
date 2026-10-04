# Results

100 decision points (dev 20 + test 80), teacher_forced, unified 11-question design.
The original five systems ran 5 repeats; the four systems added in October 2026 ran 1–5 repeats (column `reps`).
All systems: 0 failures, 100% schema pass.

## Decision level

| System | reps | scope_action | F1 | route | F1 | mode | boundary | 4-field joint | session all-correct | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Gemma 4 31B (QAT W4A16) | 5 | 87.0% | 0.812 | 90.0% | 0.853 | 92.0% | 95.0% | **77.0%** | 20.0% | 2293 | 4723 |
| Cygnet readout on Gemma 4 31B (QAT W4A16) | 1 | 80.0% | 0.748 | 86.0% | 0.797 | 92.0% | 95.0% | **69.0%** | 10.0% | 2196 | 3607 |
| Jev 1.13.0 | 5 | 85.8% | 0.881 | 90.6% | 0.871 | 91.6% | 84.4% | **61.4%** | 11.0% | 749 | 818 |
| Cygnet (Gemma-4-12B-it, vLLM 0.30.0) | 1 | 76.0% | 0.694 | 79.0% | 0.697 | 86.0% | 94.0% | **58.0%** | 10.0% | 265 | 308 |
| Clef (Cloudflare, 27B) | 2 | 86.0% | 0.876 | 85.0% | 0.803 | 88.0% | 84.0% | **54.0%** | 5.0% | 1544 | 2646 |
| djev-spark (DiffusionGemma 26B-A4B) | 5 | 51.0% | 0.324 | 69.2% | 0.638 | 80.2% | 90.4% | **32.2%** | 4.0% | 1230 | 1470 |
| Clef-flash (Cloudflare, 9B) | 5 | 72.0% | 0.666 | 82.0% | 0.760 | 77.0% | 51.0% | **28.0%** | 0.0% | 1994 | 3141 |
| SemIf (Qwen3.5-4B) | 5 | 49.0% | 0.504 | 62.0% | 0.545 | 65.0% | 91.0% | **24.0%** | 0.0% | 627 | 1206 |
| Laya 322M (8192+case_first) | 5 | 25.0% | 0.132 | 18.0% | 0.058 | 10.0% | 36.0% | **0.0%** | 0.0% | 189 | 312 |

macro-F1 ranks differently from accuracy: Jev's scope_action macro-F1 (0.881) beats Gemma's (0.812) because it is more even on the rare but safety-critical classes. Clef's (0.876) is level with Jev's.

## dev / test split

| System | all 100 | dev 20 | test 80 |
|---|---|---|---|
| Gemma 4 31B (QAT W4A16) | 77.0% | 75.0% | 77.5% |
| Cygnet readout on Gemma 4 31B | 69.0% | 70.0% | 68.8% |
| Jev 1.13.0 | 61.4% | 71.0% | 59.0% |
| Cygnet (Gemma-4-12B-it) | 58.0% | 60.0% | 57.5% |
| Clef (27B) | 54.0% | 65.0% | 51.2% |
| djev-spark (DiffusionGemma 26B-A4B) | 32.2% | 33.0% | 32.0% |
| Clef-flash (9B) | 28.0% | 25.0% | 28.8% |
| SemIf (Qwen3.5-4B) | 24.0% | 35.0% | 21.2% |
| Laya 322M (8192+case_first) | 0.0% | 0.0% | 0.0% |

## Six-field output (the package's own scorer)

| System | targets set | scope_state | six-field joint | semantic consistency |
|---|---|---|---|---|
| Jev 1.13.0 | 90.4% | 61.2% | **48.8%** | 91.2% |
| Gemma 4 31B | 90.0% | 81.8% | **72.8%** | 96.0% |
| Cygnet readout on Gemma 4 31B | 88.0% | 65.0% | **54.0%** | 92.0% |
| Clef (27B) | 84.0% | 60.0% | **44.0%** | 83.0% |
| Cygnet (Gemma-4-12B-it) | 79.0% | 59.0% | **38.0%** | 88.0% |
| Clef-flash (9B) | 81.0% | 31.0% | **18.0%** | 67.0% |
| djev-spark | 65.4% | 36.4% | **13.4%** | 88.2% |
| SemIf | 68.0% | 37.0% | **13.0%** | 55.0% |
| Laya 322M | 0.0% | 17.0% | **0.0%** | 0.0% |

## Asking first (test 80, gold route = CLARIFY)

| System | correct |
|---|---|
| Gemma 4 31B | 42.9% |
| Clef (27B) | 42.9% |
| Jev 1.13.0 | 31.4% |
| Clef-flash (9B) | 28.6% |
| Cygnet readout on Gemma 4 31B | 28.6% |
| djev-spark | 14.3% |
| Cygnet (Gemma-4-12B-it) | 0.0% |
| SemIf | 0.0% |
| Laya 322M | 0.0% |

## Determinism

Four of the original five systems are deterministic across the 5 repeats (Gemma: temperature 0 + guided decoding; SemIf and Laya: logit readout; djev varies only by vLLM nondeterminism at a fixed seed). Only Jev varies genuinely. Do not read min/max as a confidence interval.

Clef and Clef-flash are logit readouts with no sampling: their 2 and 5 repeats gave byte-identical predictions. Both Cygnet rows ran once, so their run-to-run variation (vLLM batch order can move a near-tie, as the Cygnet README notes) is not measured.

## Systems added in October 2026

All four use the same input (`bridge.state()`), the same 11 questions and the same `_assemble()` rules as `jev_redesigned`; adapters are in `code/adapters_clef_cygnet.py`.

| System | Weights | Serving | Notes |
|---|---|---|---|
| Clef | `Cloudflare/clef` (Qwen3.8-27B backbone + joint schema head), bf16 | `code/clef_server.py` (the model card's `systemone()`), transformers 5.10.2, torch 2.11, one H200 | Another model on the same GPU was paused for the run; other services still shared the GPU. |
| Clef-flash | `Cloudflare/clef-flash` (Qwen3.5-9B backbone), bf16 | same | p50/p95 are client-side through an SSH tunnel that added about 1.3 s in that session; the server-side model time was 688 / 1123 ms. |
| Cygnet | `google/gemma-4-12B-it` @ `707f0a3`, bf16 | vLLM 0.30.0 (`--max-model-len 16384 --gpu-memory-utilization 0.50`) + the recipe's unmodified `shim/decision_server.py`, T = 3.4 | Each of the 11 questions is read in its own one-token pass, all in parallel. Another model on the same GPU was paused for the run. |
| Cygnet readout on Gemma 4 31B | the same QAT W4A16 checkpoint as the Gemma row | the existing production vLLM 0.20.2 (MTP speculative decoding) + `shim/decision_server.py`, `CYGNET_MAX_PARALLEL=2` | Shares the server with live traffic, so latency is indicative only. T = 3.4 was fitted for the 12B; it does not change the argmax, so accuracy is unaffected. |

Clef's architecture uses gated-delta-net layers. The runs above used transformers' torch fallback because `flash-linear-attention` and `causal-conv1d` were not installed. A later single repeat with both installed (fla 0.5.2, causal-conv1d 1.7.0, torch 2.11 cu128) scored 56.0% and was slower (server-side p50 1798 ms vs 1286 ms), but GPU contention from co-located services varied by about as much between runs, so the effect of the fast path is not established.

Cloudflare's hosted Clef API (Workers AI) was also tried. On the free plan the 10,000-neuron daily allocation ran out after about 200 benchmark requests, so no hosted-API board is reported.
