# Jev Benchmark

Measuring how well five decision models handle multi-turn RAG routing — where to look
for an answer, and whether the conversation just changed the subject.

五個決策模型在多輪 RAG 路由上的實測：答案該去哪裡找，以及這一輪使用者是不是換了話題。

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="results/charts/leaderboard-dark.svg">
  <img alt="Routing decision accuracy by system" src="results/charts/leaderboard-light.svg" width="760">
</picture>

[English](#english) · [繁體中文](#繁體中文)

---

## English

### What is being measured

An assistant in a document-heavy workplace gets a question. Before it can answer, it has
to decide several things at once: is the answer already in the conversation, or does it
need to open a file, search a knowledge base, look something up online, or call a tool?
Should it answer, summarise, analyse, or stop and ask? And — the part that makes this
hard — did the user just change the subject, widen what counts as a relevant source, or
place a restriction that has to hold for the rest of the conversation?

That last group is what we care about most. A router that reads a single question
correctly but loses track of "only use this document" two turns later is not usable.

The test is a hundred such decision points: twenty conversations of five turns each.
Every turn comes with the history that preceded it, so each system faces exactly the
same situation. Nothing is actually fetched and no tool really runs — we are grading the
decision, not the answer.

### The results

| System | Decision correct | Route | Scope change | Restriction state | p50 | p95 |
|---|---|---|---|---|---|---|
| **Gemma 4 31B** (self-hosted) | **77.0%** | 90.0% | 87.0% | **95.0%** | 2,293 ms | 4,723 ms |
| **Jev 1.13.0** (hosted) | 61.4% | **90.6%** | 85.8% | 84.4% | **749 ms** | **818 ms** |
| djev-spark (self-hosted) | 32.2% | 69.2% | 51.0% | 90.4% | 1,230 ms | 1,470 ms |
| SemIf (self-hosted) | 24.0% | 62.0% | 49.0% | 91.0% | 627 ms | 1,206 ms |
| Laya 322M (self-hosted) | 0.0% | 18.0% | 25.0% | 36.0% | **189 ms** | 312 ms |

"Decision correct" means all four parts of the decision were right at once. Full tables,
including the benchmark's own stricter score, are in [`results/summary.md`](results/summary.md).

### What the numbers say

**Gemma and Jev are close on the decision itself and far apart on memory.** Their route
choices are within half a point of each other, and their scope-change calls within a
point. The gap is almost entirely the restriction state: 95% against 84%. That field
carries over from turn to turn, so an error there quietly poisons everything after it,
which is why Gemma gets twice as many whole conversations right.

**Jev is the predictable one.** Its slowest responses are barely slower than its typical
ones — 818 ms against 749 ms. Gemma's slowest are more than twice its typical, and over
four seconds. If you are promising a response time rather than an average, that
difference matters more than the accuracy gap.

**Nobody knows when to stop and ask.** When the request genuinely lacks something the
assistant needs, the correct move is to ask. Gemma gets that right 43% of the time and
Jev 31%, and both fail the same way: instead of asking, they go and call a tool. If a
tool has side effects — filing a ticket, sending something — the routing model cannot be
the only thing standing in front of it.

**Two of the five should not be deployed for this.** Laya answers fast and gets nothing
right; its own documentation says the base model is near chance on this kind of task
without fine-tuning. SemIf never once identified a request that should be blocked on
permission grounds — fifteen chances, zero catches.

### What we had to fix before the numbers meant anything

Five measurement faults produced completely wrong conclusions along the way, and most of
them were invisible in the scores themselves. The worst one had a system scoring 3.8%
when its real number was 32.2% — an adapter was sending Chinese text in an escaped form
that made the input five times longer, and a question count that tipped the server into
a broken answer format. Another silently turned whole runs into zeroes because an SSH
tunnel dropped and connection failures score identically to wrong answers.

The full account is in [`docs/method.md`](docs/method.md). The short version: when a
system scores badly, check that it is actually reading the input before you believe the
number.

### What is in here

| Path | Contents |
|---|---|
| [`questions/`](questions/) | The eleven questions each system is asked, and why they are split that way |
| [`results/summary.md`](results/summary.md) | Full result tables |
| [`results/per_system/`](results/per_system/) | Every prediction, timing record and score, per system per repeat |
| [`results/charts/`](results/charts/) | The leaderboard chart |
| [`docs/method.md`](docs/method.md) | How the runs were done and what can go wrong |
| [`docs/gold-audit.md`](docs/gold-audit.md) | Audit of the answer key, done before any system was run |
| [`code/`](code/) | Adapters and scoring scripts |

### Limits worth knowing

This is a scripted replay, not a live agent. Nothing branches when a system takes a
wrong turn, so a high score here does not mean a system completes real tasks. The answer
key is synthetic and has not been independently reviewed; our audit found one genuinely
arguable label and one rule the answer key follows but never states. Each conversation
is only five turns, which is far short of where memory usually fails. Self-hosted timings
share a GPU with other work and are therefore conservative.

---

## 繁體中文

### 這份測試在量什麼

一個在文件很多的職場裡工作的助理收到一個問題。在回答之前，它得同時決定好幾件事：答案是不是
已經在對話裡了，還是得開一份檔案、查知識庫、上網找，或呼叫某個工具？該直接回答、摘要、分
析，還是先停下來問清楚？而最難的部分是 —— 使用者剛剛是不是換了話題、放寬了可以參考的來源，
或是下了一個接下來整段對話都要遵守的限制？

最後那一組是我們最在意的。一個系統就算單看一題答得對，兩輪之後卻忘了「只能用這份文件」，那
就不能用。

測試是一百個這樣的決策點：二十段對話，每段五輪。每一輪都附上它之前發生過的事，所以每個系統
面對的情況完全一樣。過程中不會真的去取任何資料，也不會真的呼叫工具 —— 我們評的是決策，不是
答案。

### 結果

| 系統 | 決策正確 | 路由 | 範圍變動 | 限制狀態 | p50 | p95 |
|---|---|---|---|---|---|---|
| **Gemma 4 31B**（自建） | **77.0%** | 90.0% | 87.0% | **95.0%** | 2,293 ms | 4,723 ms |
| **Jev 1.13.0**（託管） | 61.4% | **90.6%** | 85.8% | 84.4% | **749 ms** | **818 ms** |
| djev-spark（自建） | 32.2% | 69.2% | 51.0% | 90.4% | 1,230 ms | 1,470 ms |
| SemIf（自建） | 24.0% | 62.0% | 49.0% | 91.0% | 627 ms | 1,206 ms |
| Laya 322M（自建） | 0.0% | 18.0% | 25.0% | 36.0% | **189 ms** | 312 ms |

「決策正確」指的是決策的四個部分同時答對。完整表格，包含這份測試自己那套更嚴格的計分，在
[`results/summary.md`](results/summary.md)。

### 這些數字說了什麼

**Gemma 和 Jev 在決策本身很接近，差別在記性。** 兩者的路由選擇差不到半個百分點，範圍變動的
判斷差一個百分點。差距幾乎全部來自限制狀態：95% 對 84%。這個欄位會一輪一輪傳下去，所以在
這裡出錯會悄悄污染後面每一輪 —— 這也是為什麼 Gemma 答對的完整對話數是 Jev 的兩倍。

**Jev 是可預測的那一個。** 它最慢的回應只比平常慢一點點 —— 818 毫秒對 749 毫秒。Gemma 最慢
的超過平常的兩倍，而且超過四秒。如果你承諾的是回應時間而不是平均值，這個差別比準確率的差距
更要緊。

**沒有人知道什麼時候該停下來問。** 當請求真的缺了助理需要的東西，正確的做法是問。Gemma 有
43% 的時候做對，Jev 是 31%，而且兩者錯的方式一樣：不問，直接去呼叫工具。如果那個工具有副作
用 —— 開工單、把東西寄出去 —— 路由模型就不能是它前面唯一的把關者。

**五個裡面有兩個不該用在這件事上。** Laya 答得很快，但沒有答對過；它自己的說明文件就寫著，
基礎模型在這類任務上不微調的話接近亂猜。SemIf 一次都沒有認出該因為權限而擋下的請求 —— 十五
次機會，零次抓到。

### 在數字有意義之前我們必須先修好的東西

過程中有五個量測上的毛病產生了完全錯誤的結論，而且大部分從分數本身根本看不出來。最嚴重的那
個讓某個系統拿了 3.8 分，實際上應該是 32.2 分 —— 我們的轉接程式把中文用跳脫字元送出去，讓輸
入長度變成五倍，同時題目數量剛好跨過門檻，觸發了伺服器一個會壞掉的回答格式。另一個則是
SSH 通道斷線時整輪變成零分，因為連線失敗和答錯在計分上完全一樣。

完整記錄在 [`docs/method.md`](docs/method.md)。簡短版是：當一個系統分數很難看，先確認它真的
讀到了輸入，再相信那個數字。

### 這個倉庫裡有什麼

| 路徑 | 內容 |
|---|---|
| [`questions/`](questions/) | 每個系統被問的十一道題，以及為什麼這樣拆 |
| [`results/summary.md`](results/summary.md) | 完整結果表 |
| [`results/per_system/`](results/per_system/) | 每個系統每一輪的預測、計時與評分 |
| [`results/charts/`](results/charts/) | 排行榜圖表 |
| [`docs/method.md`](docs/method.md) | 測試怎麼跑的，以及哪些地方會出錯 |
| [`docs/gold-audit.md`](docs/gold-audit.md) | 標準答案的稽核，在跑任何系統之前完成 |
| [`code/`](code/) | 轉接程式與計分程式 |

### 值得知道的限制

這是照腳本回放，不是真的 agent 環境。系統走錯路時不會有分支，所以在這裡分數高不代表它能完成
真實任務。標準答案是合成的，也沒有經過第三方覆核；我們的稽核找到一個真的有爭議的標籤，以及
一條標準答案有在遵守、但從來沒寫出來的規則。每段對話只有五輪，離記憶真正開始出問題的長度還
很遠。自建系統的時間數字是和其他工作共用同一張 GPU 量到的，因此偏保守。
