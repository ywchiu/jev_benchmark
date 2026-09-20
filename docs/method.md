# 方法與執行環境

## 測什麼

使用者目標：**量測各系統的路由／切換決策有多準**。因此主要計分口徑為「決策層級」，而非測試包預設的六欄 joint。

### 為什麼不用測試包預設的 joint 分數

`bridge.py` 把一輪決策拆成 **44 個彼此獨立的 Choice**：
- 4 個決策題：`route`、`mode`、`scope_action`、`boundary`
- 20 個 `target__*`：本輪是否需要呼叫該來源（INCLUDE/EXCLUDE）
- 20 個 `focus__*`：本輪之後焦點是否包含該來源（INCLUDE/EXCLUDE）

`evaluate.py` 的 `joint_accuracy` 要求 44 題**同時**答對。實測 Jev 的 `target__*` 單題正確率 97.3%、`focus__*` 98.2%，但 0.973^20 ≈ 0.58 — 集合全對率被 20 個獨立二元題的複利衰減主宰。實測 targets 集合全對率 60.5%，幾乎完全吻合獨立假設的預測值。

**也就是說 joint 分數量的是「集合組裝」而不是「決策品質」。** 本報告因此以 4 個決策欄位為主榜，六欄 joint 列為診斷指標。

### 決策層級指標（主榜）

| 指標 | 意義 |
|---|---|
| `scope_action` 正確率 / macro-F1 | **切換決策**：KEEP / SWITCH / EXPAND / NARROW / ASK / BLOCK |
| `route` 正確率 / macro-F1 | 9 類路由通道 |
| `mode` 正確率 | ANSWER / TRANSFORM / ANALYZE / CLARIFY / BLOCK |
| `boundary` 正確率 | auto / selected_only / internal_only |
| `decision_joint` | 上述 4 欄全部正確 |
| 整段 5 輪決策全對率 / 正確前綴長度 | 跨輪穩定度 |

計分程式：`runs/score_decision.py`（獨立於測試包，未修改 gold）。

## 資料

- multiturn v2：20 段 × 5 輪 = **100 個決策點**
- 測試包切分：**dev 20 輪**（S04/S07/S10/S15，整段切分）、**test 80 輪**（其餘 16 段）
- dev 用於串接、格式驗證與 adapter 設計；正式分數以 test 80 輪為準，dev 另外列出
- 版本凍結：`runs/DATASET_FREEZE.sha256`（在任何模型結果產生前完成）

## 回放軌道

- `teacher_forced`：每輪給相同的標準歷史與 `scope_before`，隔離當輪決策能力（主要）
- `fail_stop`：首次錯誤即停該段，未走到的輪次留在完整 gold 分母中記為未完成

## 量測協定

- 同一 client、`batch=1`、`concurrency=1`
- 先用 dev 暖機；每個 repeat 的第一次呼叫另記為冷啟動
- test 重複 **5 輪**，各輪獨立目錄保存（`runs/<system>/<split>_<track>/rep<N>/`）
- 延遲為 `run_replay.py` 量到的端到端 `predict()` 時間，含請求構造、網路、解碼與解析
- **失敗不從分母刪除**；成功延遲、失敗耗時與 timeout 分開呈現
- 原始回應全部保留於 `rep<N>/raw/`，token 用量寫入 `raw/_usage.jsonl`

## 系統與環境

| 系統 | 形態 | 版本／設定 |
|---|---|---|
| Jev | 託管 API | `jev-1.13.0`（固定版本，非 `jev-latest` 別名），`POST https://api.typesafe.ai/v1/systemone` |
| classifier.dev | 託管 API | fast tier，免費層免認證；回應 `model` 欄位實測為 `jev-1.13.0` |
| SemIf | 自建 | Qwen3.5-4B 凍結權重 + 選項 logit 讀取，MIT |
| djev → DiffusionGemma | 自建 | djev API 為 invite-only，改自建其底層 `google/diffusiongemma-26B-A4B-it`（Apache-2.0） |
| Laya | 自建 | `convaiinnovations/laya` 421M，Apache-2.0，in-process |

client：macOS（Darwin 24.6.0），經 SSH tunnel 連 H200 的本地服務。
serving：H200-1-LargitData，2× NVIDIA H200 NVL 143GB，driver 580.65.06。

## 已知的量測限制

1. **client 位置**：Jev / classifier.dev 走公網；自建模型經 SSH tunnel 連 H200。tunnel 額外延遲另行量測並標註，不混入模型本身延遲。
2. **classifier.dev 介面適配**：其 API 一次只吃一組 labels，但 `inputs` 支援批次。44 題壓成 5 次呼叫（4 個決策題各 1 次 + 40 個二元題 1 批）。每題的 instruction 字串與其他系統完全相同，僅呼叫形狀不同。此適配只施用於 classifier.dev，因為只有它有批次分類端點。
3. **Jev 機率總和容差**：`bridge.py` 的 `strict_jev` 要求 `|sum(probabilities)-1| <= 1e-5`，但 Jev 回傳的機率四捨五入到小數 2 位，合法回應可能總和為 0.99。實測 880 題中 1 題觸發（最大偏差 0.01）。這是 harness 容差設定的問題，不是模型錯誤，且 README 明載主榜只評硬標籤。因此容差改為可設定（預設 0.02），其餘嚴格檢查（題目集合、標籤合法性、值域、argmax）全部保留，並記錄在原始 1e-5 下會失敗的題數。
4. 固定腳本回放，非自由分支 agent 環境；不可宣稱為真實任務完成率。

## 洩漏檢查（實際執行的驗證）

| 檢查 | 結果 |
|---|---|
| 送入模型的 `state` 是否含 `gold` / `rationale` / `outcome_after_decision` / `expected_answers` / `split` / `session_id` / `turn_index` | **0 筆**（80 輪全檢） |
| 本輪尚未發生的工具結果或助理回覆是否出現在該輪的 `history` | **0 筆**（80 輪全檢） |
| `bridge.state()` 是否會擋下夾帶 gold 的 row | **會**：實測丟入含 `gold` 欄位的 row，正確拋出 `ValueError: Expected input-only row; metadata/gold or missing fields detected` |

`bridge.state()` 以 `set(row) != allowed` 強制輸入只能是 `{id, setup, history, scope_before, blocked_targets, user_query}`
六個欄位，多一個少一個都會拋錯，所有 adapter 都經過它建構輸入，因此洩漏在結構上被阻斷。

prompt 調整只在 dev 進行（格式驗證與 adapter 設計），test 未用於調整任何 prompt、閾值或設定。
