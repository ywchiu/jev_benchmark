# Golden Set 稽核（multiturn v2，100 決策點）

稽核於任何模型結果產生**之前**完成，資料版本已以 SHA-256 凍結於 `runs/DATASET_FREEZE.sha256`。

## 1. 資料集自洽性

| 檢查 | 結果 |
|---|---|
| 100 筆 gold 通過 `evaluate.py` 的 schema 檢查 | 100/100 |
| 100 筆 gold 通過 `evaluate.py` 的 `semantic_valid()` 跨欄位規則 | 100/100 |
| `scope_before(T_n)` == `gold.scope_after(T_{n-1})` 鏈結完整性 | 20 段全部正確 |
| `blocked_targets` 出現在 gold 的 `targets` 或 `focus_targets` | 0 筆 |
| ASK / BLOCK / KEEP 是否維持 scope 不變 | 49/49 符合 |

## 2. 標籤規則是否一致

把每一輪依 (scope_before → scope_after) 的集合關係分群，檢查同一模式是否被標成不同 `scope_action`：

| 轉換模式 | n | 標籤 |
|---|---|---|
| 焦點不變 | 49 | KEEP 40 / ASK 5 / BLOCK 4 |
| 空焦點 → 有焦點 | 13 | SWITCH 13 |
| 真子集（收斂） | 5 | NARROW 5 |
| 真超集（擴充） | 9 | EXPAND 9 |
| 不相交置換 | 12 | SWITCH 11 / NARROW 1 |
| kb → 該庫內單一文件 | 4 | NARROW 4 |
| 有焦點 → 空焦點 | 3 | SWITCH 3 |

**結論：每一種轉換模式都唯一對應一個 `scope_action`。** 唯一的多標籤群（焦點不變）完全由 `route` 決定（ASK↔CLARIFY、BLOCK↔BLOCK），且已被 `semantic_valid()` 強制。標籤規則是可學習的確定性函數，沒有自相矛盾。

## 3. 爭議案例（1 筆）

**S19-T5**（test split）

- `scope_before`: `{auto, [doc_contract]}`
- 使用者：「順便查公司現行折扣政策和星河最新未付款發票。」
- gold：`HYBRID / [kb_sales, sql_read] / SWITCH / scope_after={auto, [kb_sales, sql_read]}`
- 理由欄：「新需求確定需要知識庫與ERP兩通道。」

**爭議點**：policy.txt 的優先序寫明「同題來源增加(EXPAND) > 不同主題/返回舊題(SWITCH)」。本輪以「順便」開頭、仍在同一客戶（星河）與同一場會議準備脈絡下，合理標註者可判為 `EXPAND`，`scope_after` 保留 `doc_contract`。

**對照組 S13-T5**：「順便查核准折扣政策，**和這個狀態一起判斷下一步**。」→ gold 標 `EXPAND` 且保留原焦點。

兩者表面措辭幾乎相同，區別只在 S13-T5 明講要「和既有狀態合併判斷」。這個區分規則**沒有寫進 policy.txt**。

**修正建議**（未套用，維持凍結版本）：在 policy.txt 的 scope_action 段補一句判準，例如「『順便／另外』引入新來源時，若使用者未要求與既有來源合併判斷，視為 SWITCH；若明示合併，視為 EXPAND」。若採納，需更新版本號、gold 與 manifest 並**重測所有模型**。

## 4. 未寫進 policy 但 gold 實際採用的規則

`kb_X → doc_Y`（Y 在 X 庫內、同一主題）一律標 `NARROW`（4/4），但 `doc→doc`、`tool→doc`、`kb→tool` 等同層置換標 `SWITCH`。集合上兩者都是「不相交置換」，差別在語意上是否為「同主題的收斂」。policy.txt 只寫「NARROW=收斂來源」，未說明從知識庫收斂到庫內文件算 NARROW。這是一致的，但對模型（與人工標註者）都是隱藏規則，建議明文化。

## 5. 資料集限制（作者自述 + 本次確認）

- gold_status 為 `synthetic_author_label_not_independently_adjudicated`，尚未經雙人盲標覆核。
- 20 段 × 5 輪，涵蓋不到長對話的記憶衰減；`CONTEXT` 佔 29%，高於真實流量比例。
- dev 僅 20 輪（4 段），不是平衡集，不足以支撐微調。
- 工具回傳為固定 fixture，非自由分支環境；不可宣稱為真實任務完成率。
