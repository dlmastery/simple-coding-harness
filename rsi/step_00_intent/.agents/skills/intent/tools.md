# Tools: the checklists you perform, and their contracts

Nothing is built or run in this lesson: the two tools are checklists you go through by
reading. Every later lesson's `tools.md` states the contracts of the helpers the agent builds;
this one states the rules those helpers' `lint_pack` must implement.

## Allowed

- `validate_intent(intent.md[, acceptance.md])` - a checklist you perform by reading, not a script: the front matter has `name`, `index`, `title`, `role` (`curriculum` | `exam` | `pool`), `target`, `metric` (`roc_auc` | `roc_auc_ovr_macro`), `budget_fits` equal to 24, `models` a subset of `[logreg, rf, hgb]`, `data.kind` in `csv` | `sklearn` | `synthetic`, the line `test: locked, scored once after FREEZE`, and the five `profile_keys`; the body has the headings `What to improve`, `Why`, `What counts as success`, `What is off limits`, `The profile the verifier may condition on`. `acceptance.md` lists the 14 scorecard fields under `## The scorecard`, one `- field` line each, and its pass rule says `once` and `FREEZE`. Report every rule that fails; `ok` is true only when none does.
- `lint_pack(files, intent.md)` - every reason a pack may not run for a task, as a list of problems (empty = ok): `schema.json -> n_fits` differs from `budget_fits`; `test_rule` is not `locked, scored once after FREEZE`; `metric` or `models` differ from the intent's; `SKILL.md` lacks the front matter (`name`, `description`, `metadata.type`, `metadata.version`, `metadata.rsi`) or the headings `Boot order`, `Procedure`, `Rules`, `Done when`; `tools.md` lacks `## Allowed` or `## Forbidden`; `loop.json`, when present, is not `kind: counted_while` with `N` equal to `budget_fits`; `graph.json`, when present, has a cycle, or a path in `paths.json` uses a node that is not in the graph, walks an edge the graph does not have, or breaks a constraint (one `encode`, one `scale`, one `model` per path, `score_test` only as the last node); a verifier `SKILL.md` lacks its contract line; an `operators.md` operator lacks its guard line. A pack that widens the intent is refused before any human sees it.

## Forbidden

- load_splits, fit_recipe, score_test, save_model - nothing is trained in this lesson
- write_card, propose, apply, gate, rollback - nothing is written or changed
