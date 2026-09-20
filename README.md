# Jev Benchmark Results

**English** · [繁體中文](README.zh-TW.md)

What Is Jev? System One Models, Applications, Open-Source Ecosystem, and Benchmark Comparisons
https://www.largitdata.com/blog/jev-system-one-model-open-source-benchmark/

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="results/charts/leaderboard-dark.svg">
  <img alt="Routing decision accuracy across systems" src="results/charts/leaderboard-light.svg" width="760">
</picture>

TypeSafe introduced Jev, a hosted model that works differently from a typical text-generation model. You give it a situation and a set of choices, and instead of generating a long response, it selects one of those choices and returns a probability.

Soon after Jev was released, the community started building several open-source alternatives with a similar goal. We wanted to see how these systems compare with Jev in a realistic Agent routing scenario.

## Benchmark Scenario

We simulated an enterprise RAG Agent.

The Agent can access six knowledge bases covering company policies, products, sales, projects, and legal information. It can also open eight specific documents, such as a signed contract or an 80-page manual. In addition, it has six tools that can query ERP, CRM, and calendar data, or create a support ticket.

This benchmark does not evaluate the quality of the final answer.

Instead, it evaluates the decision that happens immediately before the answer:

**Where should the Agent get the answer from?**

When a user asks a question, the system may need to open a specific document, search a knowledge base, browse the public web, query a database, or call a tool. Sometimes it should not retrieve anything at all because the answer is already available in the conversation.

If this decision is wrong, everything downstream is likely to go wrong as well. The Agent may retrieve information from the wrong source, or answer without retrieving anything when retrieval was actually required.

For a single isolated question, this is relatively straightforward.

The real difficulty appears in multi-turn conversations.

For example, a user may first ask about a company policy, then say, “Never mind, just use this document.” Two turns later, they may switch to a completely different topic. Or they may stay on the same topic and add, “Also check the current discount.”

The system then has to decide:

Is this a new topic, or is the user simply adding another source to the same task?

This is exactly the kind of decision that routing models are designed to handle.

The benchmark contains 100 test cases across 20 conversations, with 5 turns in each conversation. Every turn includes the full conversation history up to that point.

The benchmark does not actually retrieve documents or execute tools. We only evaluate whether the system makes the correct decision. The quality of the downstream answer is not part of this benchmark.

For every turn, the system must correctly make four decisions at the same time.

### Where should the answer come from? (`route`)

The system must choose one of nine routing options:

Use information already available in the conversation, answer from general knowledge, open a specific document, search a knowledge base, search the public web, call a tool, use two source types together, ask the user for missing information, or reject the request because it is not allowed.

### Has the scope changed? (`scope change`)

This is where multi-turn conversations become difficult.

The system must choose one of six possibilities:

Nothing has changed, the user switched topics, the same task now requires an additional source, the user narrowed the scope, the available sources conflict and the system should ask before proceeding, or the request should be blocked.

For example, if the user explicitly says “Only use this file,” but the Agent still searches the entire knowledge base, that is a scope-change error.

### How should the request be handled? (`mode`)

The system must also decide whether it should:

Answer directly, rewrite or summarize, analyze or compare, ask a follow-up question, or block the request.

### What restrictions should apply next? (`restriction`)

Finally, the system must determine which source restrictions should remain active in the following turn.

For example, the Agent may be allowed to freely choose sources, restricted to only the documents explicitly selected by the user, or prohibited from using the public web.

This state persists across turns until the user explicitly removes the restriction.

That means a mistake here does not only affect the current turn. It can silently affect several later turns as well.

In the table below, **Decision Accuracy** means that all four decisions must be correct within the same turn.

## Results

| System                        | Decision Accuracy | Route     | Scope Change | Mode  | Restriction | p50        | p95        |
| ----------------------------- | ----------------- | --------- | ------------ | ----- | ----------- | ---------- | ---------- |
| **Gemma 4 31B** (self-hosted) | **77.0%**         | 90.0%     | 87.0%        | 92.0% | **95.0%**   | 2,293 ms   | 4,723 ms   |
| **Jev 1.13.0** (hosted API)   | 61.4%             | **90.6%** | 85.8%        | 91.6% | 84.4%       | **749 ms** | **818 ms** |
| djev-spark (self-hosted)      | 32.2%             | 69.2%     | 51.0%        | 80.2% | 90.4%       | 1,230 ms   | 1,470 ms   |
| SemIf (self-hosted)           | 24.0%             | 62.0%     | 49.0%        | 65.0% | 91.0%       | 627 ms     | 1,206 ms   |
| Laya 322M (self-hosted)       | 0.0%              | 18.0%     | 25.0%        | 10.0% | 36.0%       | **189 ms** | 312 ms     |

p50 represents a typical response latency.

p95 represents the slower end of the latency distribution. In simple terms, roughly 19 out of 20 requests complete faster than this value.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="results/charts/decisions-zh-dark.svg">
  <img alt="Comparison of three out of the four routing decisions" src="results/charts/decisions-zh-light.svg" width="900">
</picture>

The chart above compares three of the four decision dimensions using the same scale.

`mode` is not included because Gemma and Jev differ by less than half a percentage point on that dimension, so there is very little meaningful separation.

The more interesting pattern appears elsewhere.

Gemma and Jev are very close on `route` and `scope change`. Most of the overall gap comes from the third dimension shown here: restriction-state updates.

The full results, including the stricter scoring method used by this benchmark, are available in [`results/summary.md`](results/summary.md).

## What Do These Numbers Tell Us?

### Gemma and Jev are very close on routing. The real difference is state updates.

If we look only at the core routing decisions, Gemma and Jev are nearly tied.

Their `route` accuracy differs by less than half a percentage point, and their `scope change` accuracy differs by only about one percentage point.

The overall gap between 77.0% and 61.4% comes mainly from `restriction`.

Gemma reaches 95.0% accuracy on this dimension, while Jev reaches 84.4%.

It is important to clarify that this is not a memory problem.

Every system receives the complete conversation history.

By the fifth turn, the input contains all previous user questions, tool results, and assistant responses, for a total of eleven messages. The currently active restriction is also explicitly included in the input.

The model does not need to remember the previous state on its own.

Its actual task is:

**Given the current restriction, determine what the restriction should become after this turn.**

Jev is less accurate at that transition.

And because `restriction` state carries forward into the next turn, one incorrect update can affect the rest of the conversation.

This also helps explain why Gemma completes roughly twice as many full conversations without making any decision errors.

Since the current state is already explicitly provided to the model, simply adding more context does not solve this problem.

### Jev has much more predictable latency

One of Jev's strongest advantages is latency consistency.

Its p50 latency is 749 ms, while its p95 is 818 ms.

That means the difference between a typical request and a relatively slow request is only about 70 ms.

Gemma has a p50 of around 2.3 seconds, while its p95 exceeds 4.7 seconds.

So if a production system cares not only about average latency, but also about keeping decision time predictable across requests, Jev's latency profile is very attractive.

### None of the systems are particularly good at knowing when to stop and ask

Another clear weakness is deciding when the Agent should ask the user for more information instead of proceeding.

Some requests are missing information that the Agent genuinely needs. In those cases, the correct action is not to search or call a tool. It is to ask a follow-up question first.

Gemma gets only 43% of these cases right. Jev gets 31%.

More importantly, both systems tend to fail in the same way:

**They skip the question and call a tool directly.**

If that tool only reads data, the risk may be limited.

But if the tool has side effects, such as creating a ticket, sending a message, or modifying data, the routing model should not be the only safety gate in front of execution.

An additional validation or permission layer is still necessary before side-effecting tools are allowed to run.

### Some models are not ready for this type of routing task

Laya is extremely fast, with a p50 latency of only 189 ms.

However, its full decision accuracy in this benchmark is 0%.

Its own documentation also notes that the base model performs close to random guessing on this type of task without task-specific fine-tuning.

SemIf has a different weakness.

It performs particularly poorly on permission and rejection decisions.

There are fifteen benchmark cases where the correct behavior is to reject the request because of permissions or policy constraints. SemIf fails to identify all fifteen of them.

So while both systems are fast, neither is currently suitable as the primary routing layer for an enterprise Agent without additional work.

## Reference Files

| Path                                         | Description                                                                             |
| -------------------------------------------- | --------------------------------------------------------------------------------------- |
| [`questions/`](questions/)                   | The eleven questions used for each system and why the benchmark was structured this way |
| [`results/summary.md`](results/summary.md)   | Full benchmark results                                                                  |
| [`results/per_system/`](results/per_system/) | Per-turn predictions, latency, and scores for each system                               |
| [`results/charts/`](results/charts/)         | Charts used above                                                                       |
| [`docs/method.md`](docs/method.md)           | Benchmark methodology and known failure modes                                           |
| [`docs/gold-audit.md`](docs/gold-audit.md)   | Audit of the golden answers, completed before running any system                        |
| [`code/`](code/)                             | Adapter and scoring code                                                                |
