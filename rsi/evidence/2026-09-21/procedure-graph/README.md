# One edge changes the executed route

Author walkthrough of lab 10.28, 21 September 2026. The [protocol](PROTOCOL.md) preceded execution. The agent created the runner and fixtures; no student wrote code.

The [parent graph](parent.md) sends invalid input to a fit stub. The [child graph](child.md) changes that one edge to diagnosis. The runner reads these Markdown tables, so the edit changes execution rather than only a drawing.

| Check | Evidence |
|---|---|
| Invalid selection case | [Parent trace](selection-invalid-parent/TRACE.csv) reaches the stub; [child trace](selection-invalid-child/TRACE.csv) reaches diagnosis |
| Valid regression case | [Parent](selection-valid-parent/TRACE.csv) and [child](selection-valid-child/TRACE.csv) both retain reporting |
| Later calendar fixture | [Frozen graph](FREEZE.md) reaches [reporting](later-calendar/TRACE.csv) |
| Numeric target component | [Type check passes](later-semantic/TRACE.csv), then the [unchanged domain check rejects it](later-semantic/DOMAIN-CHECK.md) |

The two selection pairs account for four traversals. The later cases add two. There was one proposed edit, four fixture comparisons, six graph traversals, and **zero model fits**. The accepted edit passed the declared rule; no rejected child was invented. The failing parent trace remains available.

Each traversal folder contains an input, domain facts, node records written before actions, and an actual trace. The [cost ledger](COST.csv) includes measured wall time and subprocess startup. Agent inference cost is unknown. The [manifest](MANIFEST.csv) hashes the retained run files; all 66 original workspace files, including the manifest, were copied and hash-checked.

This demonstrates deterministic routing and a separate meaning check. The fixtures are author-constructed in one context. The later fixture is distinct and created after freezing, but is not blinded transfer evidence. The domain checker trusts supplied facts and checks only its declared rules. No independent coding agent, paper reproduction, or learner assessment is established.

The [driver snapshot](run-procedure-graph.mjs) records the exact implementation. Its maintained source is in the [authoring scripts](../../../../how-did-i-generate-it/rsi/scripts/run-procedure-graph.mjs); it refuses to overwrite its original sibling run folder. Re-execution needs a newly declared destination and budget.
