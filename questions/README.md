# The eleven questions / 十一道題目

[English](#english) · [繁體中文](#繁體中文)

## English

Every turn of the conversation, each system is asked the same eleven questions about
what the assistant should do next. The full text of each question, and every option it
offers, is in `questions.json`.

### What the questions are for

The benchmark wants six pieces of information out of every turn: where to look for the
answer, how to process it, which specific sources to fetch, whether the working scope
changed, what restriction applies afterwards, and which sources stay in focus. Four of
those are a single choice from a short list, so they map onto one question each. The
other two are *sets* — "which sources do I need this turn" can be nothing, one source,
or a handful.

That is the awkward part. The hosted models being tested answer one question with one
answer; they cannot hand back a list. So the set has to be assembled from several
single answers, and how you split it up turns out to matter a lot.

### How we split it

We looked at what the answers actually are before deciding. Across the hundred turns,
the set of sources to fetch is empty almost half the time, a single source in most of
the rest, occasionally two, and never more than two. Meanwhile the benchmark's own rule
book already sorts every source into one of four kinds: documents, knowledge bases, the
public web, and tools.

So instead of asking "do I need this source? do I need that one?" twenty times over, we
ask once per kind. Three questions cover any answer the data actually contains, and a
request that needs two kinds at once falls out naturally as the union of two answers.

| Question | Options | What it asks |
|---|---|---|
| `route` | 9 | Which channel this request goes to |
| `mode` | 5 | Answer, rewrite, analyse, ask, or block |
| `scope_action` | 6 | Did the working scope stay, switch, widen, narrow, need asking, or get blocked |
| `boundary` | 3 | What source restriction applies after this turn |
| `targets_doc` | 9 | Which document to open, if any |
| `targets_kb` | 7 | Which knowledge base to search, if any |
| `targets_tool` | 6 | Which tool to call, if any |
| `focus_doc` | 9 | Which document stays in focus afterwards |
| `focus_kb` | 7 | Which knowledge base stays in focus |
| `focus_tool` | 7 | Which tool stays in focus |
| `focus_keep_before` | 2 | Whether the previous focus is kept as well |

No question offers more than nine options. That ceiling is not cosmetic: one of the
systems refuses anything outside two to sixteen options, and another squeezes its
options into a fixed token budget, so a design with long option lists simply cannot run
everywhere.

### Putting the answers back together

Five rules turn the eleven answers into the six fields. Every one of them is written in
the benchmark's own rule book, so none of them is us feeding the model an answer:

1. If the route is "use what we already have", "general knowledge", "ask first", or
   "blocked", then nothing gets fetched. The rule book says so outright.
2. If the route is the public web, the source is the web search tool, because the
   catalogue contains exactly one.
3. If the route names one kind, only that kind's answer counts; answers for the other
   kinds are ignored, so a stray mark cannot produce a contradictory result.
4. If the route is the mixed one, take everything that was marked.
5. If the scope decision was "ask first" or "blocked", the scope does not move. Again,
   straight from the rule book.

We checked how much these rules are worth by removing them one at a time. At most they
account for six points of one system's score, and for another system removing all of
them changes nothing at all, because its own answers already obeyed them.

### The one thing this design cannot express

Each kind gets one pick, so two documents in the same turn, or two tools in the same
turn, cannot be expressed. Two of the hundred turns need exactly that. The design
therefore tops out at 97 out of 100 rather than a perfect score, and any comparison
should keep that ceiling in mind.

---

## 繁體中文

對話的每一輪，每個系統都會被問同樣的十一道題，問的是「助理接下來該做什麼」。每一題的完整
文字和所有選項都在 `questions.json` 裡。

### 這些題目在問什麼

這份測試要從每一輪得到六個資訊：去哪裡找答案、怎麼處理、要取用哪些具體來源、工作範圍有沒有
變動、之後受什麼限制、以及焦點留在哪些來源上。其中四個是從一份短清單裡挑一個，所以各對應
一題。另外兩個是**集合** —— 「這一輪需要哪些來源」可能是沒有、一個，也可能是好幾個。

麻煩的地方就在這裡。受測的託管模型一題只回一個答案，沒辦法交回一份清單。所以集合必須用好幾
個單一答案拼出來，而怎麼拆，結果差很多。

### 我們怎麼拆

決定之前先看了答案長什麼樣子。一百輪裡面，要取用的來源將近一半是空的，其餘大多只有一個來
源，偶爾兩個，從來沒有超過兩個。而這份測試自己的規則書本來就把每個來源歸進四類：文件、知
識庫、公開網路、工具。

所以與其問二十次「要不要這個來源、要不要那個」，我們改成每一類問一次。三題就涵蓋了資料裡
實際出現的所有答案，而需要跨兩類的請求，自然就是兩個答案的聯集。

| 題目 | 選項數 | 問什麼 |
|---|---|---|
| `route` | 9 | 這個請求走哪條路 |
| `mode` | 5 | 回答、改寫、分析、追問，還是擋下 |
| `scope_action` | 6 | 工作範圍是維持、換題、擴大、收斂、該先問，還是被擋 |
| `boundary` | 3 | 這一輪之後適用什麼來源限制 |
| `targets_doc` | 9 | 要開哪一份文件（如果需要） |
| `targets_kb` | 7 | 要查哪一個知識庫（如果需要） |
| `targets_tool` | 6 | 要呼叫哪一個工具（如果需要） |
| `focus_doc` | 9 | 之後焦點留在哪一份文件 |
| `focus_kb` | 7 | 之後焦點留在哪一個知識庫 |
| `focus_tool` | 7 | 之後焦點留在哪一個工具 |
| `focus_keep_before` | 2 | 要不要同時保留原本的焦點 |

沒有任何一題超過九個選項。這個上限不是為了好看：其中一個系統拒絕接受二到十六個以外的選項
數，另一個則把選項壓在固定的字數預算裡，所以選項清單太長的設計根本沒辦法在所有系統上跑。

### 怎麼把答案拼回去

五條規則把十一個答案變成六個欄位。每一條都寫在這份測試自己的規則書裡，所以沒有一條是我們
在餵答案給模型：

1. 如果路由是「用現有的內容就好」「一般常識」「先問清楚」或「擋下」，那就什麼都不取。規則
   書明文寫著。
2. 如果路由是公開網路，來源就是網路搜尋工具，因為整份目錄裡只有這一個。
3. 如果路由指定了某一類，就只採用那一類的答案，其他類的忽略，這樣就算模型在別類上誤勾，也
   不會產生互相矛盾的結果。
4. 如果路由是混合型，就把所有被勾選的都取用。
5. 如果範圍決策是「先問清楚」或「被擋下」，範圍就不動。一樣來自規則書。

我們把這些規則一條一條拿掉重算，看它們到底值多少分。結果是最多只占某個系統六分，而另一個
系統全部拿掉分數完全不變，因為它自己的答案本來就符合這些規則。

### 這個設計唯一表達不了的事

每一類只能挑一個，所以同一輪要兩份文件、或同一輪要兩個工具，就表達不出來。一百輪裡剛好有兩
輪需要這樣。因此這個設計的上限是一百分裡的九十七分，不是滿分，任何比較都應該把這個天花板
放在心上。
