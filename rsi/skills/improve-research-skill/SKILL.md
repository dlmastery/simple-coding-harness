---
name: improve-research-skill
description: Propose and evaluate one change to an ML research procedure, retaining parent and child instructions and evidence of later use. Use for self-improvement and bounded RSI course experiments.
---

# Improve a research skill

Read the lesson, task contract, parent skill, and complete prior experiment ledger. Identify one observed failure in how experiments were proposed, diagnosed, allocated, or selected. Do not use final evaluation cases to design the change.

Write `CHANGE-PROPOSAL.md`: failure, evidence, one proposed procedural change, expected effect, risk, allowed budget, and a falsifying observation. Preserve the parent skill. Save a versioned child skill; do not overwrite ancestry.

Distinguish two targets. A task skill tells the solver how to do ML research. An improver skill tells a process how to propose and evaluate changes to those task skills. State which target this change affects. Do not call a new model setting an improver revision.

An improver's internal proposal-ranking or promotion rule can be the proposed change. Keep the external comparison that judges this changed improver fixed: its tasks, data roles, metric, resource allocation, and final acceptance criterion. Do not confuse a legitimate internal rule revision with changing the external definition of success after seeing results.

Use a fresh execution context for each parent/child comparison when the host supports it. Otherwise label the same-context comparison and its contamination risk. Give each the same starting artifacts and declared resources. Charge proposal work, validation, retries, failed attempts, and model fitting. If agent costs are unavailable, narrow the conclusion accordingly.

Evaluate the retained child and its parent on prespecified selection tasks. Keep unsuccessful and harmful edits. Do not promise a gain. Only promote under the declared acceptance rule. Freeze a promoted skill before later evaluation.

To demonstrate inheritance, start a later improvement round with the selected improver, read its exact version, and record which instruction governed a new proposal or check. Save parent and child hashes and a behavioral trace. A file dependency proves structural lineage; an observed changed decision supports actual use.

To assess effectiveness, compare improvements produced by the two improvers on fresh tasks under matched resources. A better solver score does not alone show a better improver. Do not claim acceleration without repeated generational evidence and total cost accounting.

Check the effective behavior of composed changes. A new recipe name or different source hash can still construct the same model: a later parameter assignment may overwrite an earlier edit. Inspect the complete model and preprocessing settings before allocating a future comparison. Keep construction checks separate from measured model fits. If this problem is discovered after an experiment is frozen, report it and preserve every charged attempt; do not replace outcomes or silently extend the budget.

Include a credible conventional search control as well as the parent procedure. Beating the parent does not imply beating that control. Report predictive differences, actual executed work and uncertainty separately. For a worked six-procedure comparison, read `rsi/experiments/real-tabular/comparison/README.md` and inspect its evidence before proposing another run.

Check that an operator does what its name promises. A higher-capacity tree proposal must not impose a new finite depth cap on an unlimited parent. Parameter clipping can also make a proposed change identical to its parent. Preserve integer-versus-fraction semantics when comparing settings. The checked example in `rsi/experiments/real-tabular/refinement-v2/README.md` separates constructor changes, prediction changes and measured quality.

Stop at the lesson's generation limit. Return a lineage table, results, costs, rejected changes, and a claim audit. Never replace a failed experiment with invented success.

When the claim concerns improvement of a whole researcher, evaluate its complete search loop. A saved list of candidate settings is narrower evidence. Preserve the executable parent and child, the improver that generated the child, and a later run that consumes that source. Count losing inner searches as outer research cost. The [bounded worked example](../../experiments/real-tabular/nested/README.md) shows actual inherited rewriting and inconclusive transfer; its 624-attempt author budget does not override a learner's smaller lesson budget.
