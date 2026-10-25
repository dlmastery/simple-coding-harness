# What the four attempts show

All four forms passed the exact checker. Each preserved the initially correct fields and made one repair. The action-hint, observation, and fresh conditions each used one inspection; the stale-hint condition used two.

| Condition | Actual actor actions | Checked result |
|---|---|---|
| Action hint | Inspect Split; see empty; set chronological; check | Pass |
| Observation | Inspect Split; see empty; set chronological; check | Pass |
| Fresh, unassisted | Inspect Dataset; see empty; set wine; check | Pass |
| Stale hint with accurate observation | Inspect Split; see chronological; inspect Metric; see empty; set MAE; check | Pass |

The first two packets supply different help about identical initial forms. One recommends an operation; the other describes a missing value. Required task values are visible in both. The accurate observation in the stale condition points to Metric, while the outdated action hint points to Split. Following that hint first creates a detour without corrupting the completed form.

The current coding agent chose and invoked every recorded inspection and repair. The controller only returned field values, enforced the local budget, applied the requested repair, and checked the result. No automatic solver chose actions. Each tool output was read before the next action decision; a repair and its final check were sometimes issued sequentially in the same shell call.

The author wrote all fixtures, saw their answers, and used one conversation. In the fresh condition, Dataset was both the first listed field and the author-known missing field. Its one-inspection success is not a fair measure of unguided discovery. The stale detour was deliberately planned before execution. Four successes do not establish a causal benefit, unassisted learning, or reliable recovery in a new agent session.

The forms are illustrative experiment metadata, not dataset measurements. They do not train or fit a model. Field-inspection counts describe this small interface only. The source paper studies a training mechanism that this activity does not reproduce.
