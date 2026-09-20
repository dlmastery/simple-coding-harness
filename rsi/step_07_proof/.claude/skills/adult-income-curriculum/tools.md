# Tools: the helpers you build, and their contracts

Two helpers of its own; the actor's and the verifier's are built by their packs' procedures and run as those packs.

## The runtime you build (shared by every tool)

No script is shipped. Every tool below is a contract; you implement it once, on first use,
under `runs/<pack name>/helpers/` (Python with scikit-learn is the natural choice - the CSV
and the sklearn built-ins are named in the problem's `intent.md`; any language that can read a
table and fit these three models is fine) and run it through your Bash tool from this
lesson's directory. Reuse a helper that exists; do not rewrite it. Every tool prints one JSON
object and exits 0 even when it refuses: a refusal is `{"error": "..."}` (or `refused` on one
item) that you read, never a crash you retry.

- **Paths.** `<pack>` is the skill directory (`.claude/skills/<pack name>`); `<task>` is the
  problem's directory under `../tasks/`, whose `intent.md` front matter gives `name`, `target`,
  `metric`, `budget_fits`, `models`, `data`, `role`. One arm of one problem lives in
  `runs/<pack name>/<task name>/<arm>/` - `<arm>` is `memory` or `control` (a lesson may name
  others), with `-s<seed>` appended when the seed is not 0.
- **State.** `state.json` in the arm directory:
  `{"arm", "seed", "problem", "n_fits": 24, "fits_used": 0, "frozen": false, "test_scored": 0, "test_score": null, "test_recipe": null, "memory": "on" | "off" | "frozen"}`,
  written with `json.dump(..., indent=1)` so the freeze is the literal text `"frozen": true`
  (the lesson's hook greps `runs/` for it before it lets a `score_test` command run).
- **Trace.** `traces.jsonl` next to it, append-only, one JSON object per line: a fit row
  `{"t": n, "arm", "seed", "problem", "recipe", "val_score", "error"}` and event rows
  `{"event": "open" | "FREEZE" | "score_test" | "scorecard" | "write_card" | "propose" | "apply" | "gate" | "rollback", ...}`
  (`scorecard` is the scorecard tool's own event; `write_card` is the verifier's and appears only when a
  card was written). Never rewrite or delete a line.
- **Data.** `data.kind: csv` reads `data.path` relative to the series root (`..` from this
  lesson); `kind: sklearn` is `sklearn.datasets.load_<name>()` as a frame with the feature
  names and an integer `target`; `kind: synthetic` is
  `sklearn.datasets.make_classification(**params)` with the parameters listed in the front
  matter (`random_state` included), columns `x0..`, integer `target`. Non-numeric columns are
  strings with `"missing"` for NaN; the target is an int.
- **Profile.** `{"n_rows", "n_features"` (columns minus the target)`, "n_classes", "imbalance"`
  (the share of the rarest class, 3 decimals)`, "has_categorical"` (0 / 1)`}` over the whole table.
- **Split.** `order = numpy.random.default_rng(seed).permutation(n_rows)`; train = the first
  55 %, val = the next 15 %, private = the next 10 %, test = the last 20 % (cuts at
  `int(n * 0.55)`, `int(n * 0.70)`, `int(n * 0.80)`). The same seed gives the same rows on
  every machine. Only `score_test` may read the test part; only `private_score` the private part.
- **Recipe.** Exactly `{"model", "hyper", "scale", "encode", "class_weight"}` with values from
  `schema.json -> fields` (`hyper` from the model's own list; the middle value is the default:
  logreg 1, rf 16, hgb 0.1). Pipeline: `ColumnTransformer(..., sparse_threshold=0)` (dense
  output: the boosting model takes no sparse matrix) with `StandardScaler` (scale `yes`)
  or passthrough on the numeric columns and `OneHotEncoder(handle_unknown="ignore")` (encode
  `onehot`) or `OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)` on the
  categorical ones, then `LogisticRegression(C=hyper, max_iter=2000)` |
  `RandomForestClassifier(n_estimators=40, max_depth=hyper, random_state=0)` |
  `HistGradientBoostingClassifier(learning_rate=hyper, max_iter=40, max_bins=64, random_state=0)`,
  with `class_weight="balanced"` or `None`. Metric `roc_auc` = ROC-AUC of the positive-class
  probability; `roc_auc_ovr_macro` = one-vs-rest macro ROC-AUC over `predict_proba`. Round
  `val_score` to 4 decimals; silence scikit-learn's warnings (a convergence warning is not an
  error). A fit that raises is a result too - `val_score` null, `error` `"<Type>: <message>"` -
  and it still counts against the budget.
- **Two mirrors, one pack.** Every file a tool changes inside a pack (`memory.json`,
  `SKILL.md`, `schema.json`, `roles/`, ...) changes in `.claude/skills/<pack name>/` and in
  `.agents/skills/<pack name>/` alike; `write_card`, `apply`, `gate`, `rollback` and
  `skill_memory` write both.

## Allowed

- `curve(pack, tasks)` - for every curriculum problem (`role: curriculum`, index order) with both arms scored, the row `problem, memory_best_val, control_best_val, gap_val (memory - control), wasted_memory, wasted_control (fits each arm spent before reaching the control arm's best val within 0.005), cards_added, cards_demoted, cards_active`; a problem without both scorecards is listed as `missing`, never invented. Write `runs/<pack name>/curve.json` and print the table.
- `exam(pack, task, seeds)` - for the exam problem, per seed: both arms' `test_score`, `wasted_fits`, the winner (higher test score, or the same score with fewer wasted fits); `wins` out of the seeds, `mean_test_gap` (memory - control), `not_transferred`: every card that applied whose preferred value is absent from the memory arm's best recipe on that seed; `pack_unchanged` (sha256 of `memory.json` before the first exam arm equals the one after the last) and `no_card_written` (no `write_card` event in any exam trace). Write `runs/<pack name>/exam.json`, print the table.

## Forbidden

- write_card - the verifier's pen; the curriculum skill only asks the verifier to use it
- propose, apply, gate, rollback - the curriculum skill changes no pack; a meta pack does, in lesson 09 on
