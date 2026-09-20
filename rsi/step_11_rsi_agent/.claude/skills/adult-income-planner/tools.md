# Tools: the helpers you build, and their contracts

One helper that reads the arm's fits by family and writes the plan the actor runs.

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

- `write_plan(pack, task, target, plan)` / `write_plan(..., uncertainty=True, c=<c>)` - with `uncertainty`: per model family on this problem's memory arm, `n` (fits so far), `wins` (val at or above the first fit's), `success = (wins + 1) / (n + 2)`, `faults` (fits below the first fit's, or errored) and `u = (1 - success) + c / (n + 1)`; print them. With `plan`: refuse a plan without `phase` (`broad` | `deep`), `c` and exactly 12 `experiments` from `schema.json -> fields`, refuse a second plan in the same phase on the same problem; write it to `<target>/plan.json` (both mirrors), append `{"event": "plan", "phase", "c"}` and print the families in order.
- `read_memory(pack, task, arm, order=None)` - the cards of `<pack>/memory.json` (none when the arm's state says memory `off`), which of them apply - the `if` holds for the profile (`key op value`) and the card is active (`evidence >= 1` and `counter * 2 < evidence`) - the `preferred` value per field (among the applicable `prefer` cards of that field the one with the largest `evidence - counter`; a tie is no preference) and the `forbidden` values; with `order=<policy>` also `next`: the next eight recipes of that policy given the arm's fits so far (see the policies).

## Forbidden

- fit_recipe, score_test, save_model, load_splits - the planner chooses experiments and runs none
- write_card, propose, apply, gate - not the planner's
