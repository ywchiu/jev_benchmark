# The eleven questions

**English** · [繁體中文](README.zh-TW.md)

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
