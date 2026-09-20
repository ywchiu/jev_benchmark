# Results

100 decision points (dev 20 + test 80) x 5 repeats, teacher_forced, unified 11-question design.
All systems: 0 failures, 100% schema pass.

## Decision level

| System | scope_action | F1 | route | F1 | mode | boundary | 4-field joint | session all-correct | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| Gemma 4 31B (QAT W4A16) | 87.0% | 0.812 | 90.0% | 0.853 | 92.0% | 95.0% | **77.0%** | 20.0% | 2293 | 4723 |
| Jev 1.13.0 | 85.8% | 0.881 | 90.6% | 0.871 | 91.6% | 84.4% | **61.4%** | 11.0% | 749 | 818 |
| djev-spark (DiffusionGemma 26B-A4B) | 51.0% | 0.324 | 69.2% | 0.638 | 80.2% | 90.4% | **32.2%** | 4.0% | 1230 | 1470 |
| SemIf (Qwen3.5-4B) | 49.0% | 0.504 | 62.0% | 0.545 | 65.0% | 91.0% | **24.0%** | 0.0% | 627 | 1206 |
| Laya 322M (8192+case_first) | 25.0% | 0.132 | 18.0% | 0.058 | 10.0% | 36.0% | **0.0%** | 0.0% | 189 | 312 |

macro-F1 ranks differently from accuracy: Jev's scope_action macro-F1 (0.881) beats Gemma's (0.812) because it is more even on the rare but safety-critical classes.

## dev / test split

| System | all 100 | dev 20 | test 80 |
|---|---|---|---|
| Gemma 4 31B (QAT W4A16) | 77.0% | 75.0% | 77.5% |
| Jev 1.13.0 | 61.4% | 71.0% | 59.0% |
| djev-spark (DiffusionGemma 26B-A4B) | 32.2% | 33.0% | 32.0% |
| SemIf (Qwen3.5-4B) | 24.0% | 35.0% | 21.2% |
| Laya 322M (8192+case_first) | 0.0% | 0.0% | 0.0% |

## Six-field output (the package's own scorer)

| System | targets set | scope_state | six-field joint | semantic consistency |
|---|---|---|---|---|
| Jev 1.13.0 | 90.4% | 61.2% | **48.8%** | 91.2% |
| Gemma 4 31B | 90.0% | 81.8% | **72.8%** | 96.0% |
| djev-spark | 65.4% | 36.4% | **13.4%** | 88.2% |
| SemIf | 68.0% | 37.0% | **13.0%** | 55.0% |
| Laya 322M | 0.0% | 17.0% | **0.0%** | 0.0% |

## Determinism

Four of five systems are deterministic across the 5 repeats (Gemma: temperature 0 + guided decoding; SemIf and Laya: logit readout; djev varies only by vLLM nondeterminism at a fixed seed). Only Jev varies genuinely. Do not read min/max as a confidence interval.

