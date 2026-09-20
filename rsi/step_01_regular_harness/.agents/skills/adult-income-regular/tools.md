# Tools: the helpers you build, and their contracts

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

- `load_splits(pack, task, arm="memory", seed=0, memory="on")` - read the table, compute the profile and the split, create the arm directory and its `state.json` (refuse when the arm is already open: an arm is opened once), append `{"event": "open"}` to the trace, and print the profile, the budget and, for a memory arm, the cards that apply (as `read_memory` lists them). `memory="off"` (the control arm, or `config.md` saying `memory: off`) records `"memory": "off"` in the state: no card is read or written on this arm.
- `fit_recipe(pack, task, arm, recipes)` - for each recipe of the list, in order: refuse (no fit, `"refused": "..."` on that item) a recipe outside `schema.json -> fields`, one an active `forbid` card rules out (memory arms only), or one this arm already fitted; refuse every item once `fits_used` is `n_fits` (`"error": "budget: 24 fits used"`); otherwise fit on train, score on val, append the fit row and add one to `fits_used` (an errored fit counts). The moment `fits_used` reaches `n_fits`, write `"frozen": true` and append `{"event": "FREEZE"}`. Print `results` (each with `n`, `recipe`, `val_score`, `error`), `fits_left` and `FREEZE` (true / false). Refuses the 25th call by reading `state.json`, not by counting in memory.
- `score_test(pack, task, arm, recipe)` - refuse unless `state.json` says `"frozen": true` (`"error": "the test split is locked until FREEZE"`); refuse when `test_scored` is already 1 (`"error": "scored once already"`); refuse a recipe this arm never fitted. Otherwise fit it again on train (deterministic), score the test part, write `test_score`, `test_recipe`, `test_scored: 1`, append `{"event": "score_test", "recipe", "test_score"}`, print them.
- `save_model(pack, task, arm, recipe)` - pickle the recipe's fitted pipeline to `model.pkl` in the arm directory; refuse before FREEZE and refuse a recipe the arm never fitted.
- `scorecard(pack, task, arm)` - write `scorecard.json` in the arm directory with exactly the 14 fields of lesson 00's `acceptance.md` - `problem`, `arm`, `seed`, `n_fits`, `fits_used`, `wasted_fits` (the fits before the first one within 0.005 of the arm's best `val_score`, plus every errored fit), `best_val_score`, `best_recipe`, `test_score`, `test_scored_once` (`test_scored == 1`), `test_touched_before_freeze` (true if a `score_test` event precedes the `FREEZE` event in the trace), `cards_active`, `cards_added`, `cards_demoted` (the pack's `memory.json` now; 0 for a pack without one) - and print it.

## Forbidden

- read_memory, write_card, read_traces - this pack has no memory and no verifier
- propose, apply, gate, rollback - this pack changes no file
