# An outdated hint can cause a detour

In [lab 10.33](../../../10_research_studio/10_feedback_and_transfer/step_33_scaffolding/README.md), an action hint recommends what to inspect next. An enriched observation describes the current form. The distinction matters when the form changes.

Four author-operated attempts passed their exact checks. The first three used one field inspection each. In the fourth, deliberately following an outdated Split hint added an inspection before the missing Metric field was repaired. Each attempt made one repair and preserved initially correct fields.

| Condition | Packet | Actions | Exact check |
|---|---|---|---|
| Action hint | [Task and hint](action/PACKET.md) | [Trace](action/TRACE.csv) | [Pass](action/CHECK.md) |
| Richer observation | [Task and state](observation/PACKET.md) | [Trace](observation/TRACE.csv) | [Pass](observation/CHECK.md) |
| Fresh, unassisted | [Changed task](fresh/PACKET.md) | [Trace](fresh/TRACE.csv) | [Pass](fresh/CHECK.md) |
| Stale hint | [Conflicting help](stale/PACKET.md) | [Trace](stale/TRACE.csv) | [Pass](stale/CHECK.md) |

The actor was the current coding agent. It invoked inspection and repair commands; the controller did not choose actions. The author also designed the fixtures and knew their contents. The fresh task changed the form, but did not receive a fresh agent context. The stale detour was preplanned. These traces illustrate assistance types; they cannot establish learned capability or a causal advantage of one method.

Read the [full interpretation](ASSISTANCE-REPORT.md), [predeclared protocol](PROTOCOL.md), [source audit](SOURCE-AUDIT.md), [resource record](COST.md), and [unattempted learner checkpoints](LAB-NOTE.md). No fits or weight updates occurred. The existing lesson infographic is conceptual, not a measured chart.

The [manifest](MANIFEST.csv) contains 29 original files, checked against both the sibling workspace and this archive. This guide and the manifest itself are publication additions outside the manifest's file list. The [frozen input identities](FROZEN.csv), [controller snapshot](run-scaffolding.mjs), and per-condition original/state files preserve the mechanism.

For a new attempt, use the lesson prompt and a new sibling workspace. Maintainers can invoke the canonical [controller source](../../../../how-did-i-generate-it/rsi/scripts/run-scaffolding.mjs) from the repository root: prepare a new destination, then explicitly choose inspect, repair, and check commands. Never rerun an archived attempt to reset its budget. The local guard is procedural; an author with filesystem access can bypass it.
