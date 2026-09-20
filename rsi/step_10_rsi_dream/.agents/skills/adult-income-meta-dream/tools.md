# Tools: the helpers you build, and their contracts

The simulator is the log: `rank_policies` replays it and spends nothing.

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

- `rank_policies(pack, task, target, policies)` - replay the last problem's memory-arm log as a simulator: for each policy of `policies.md`, walk its first 24 picks (from the cards and, step by step, the picks answered so far); a pick the log holds is answered with the logged `val_score`, a pick the log does not hold is `unknown` and answered with nothing. A policy's score is the best logged val among its picks; at a tie the policy with more unknown picks ranks higher (a lap that only revisits the log learns nothing). No fit is spent: `fits_spent: 0`, and the target's `state.json` is unchanged. Print the ranking (`policy, best_logged_val, visited, unknown`), `winner`, and `saturated` (true when every policy's unknown count is 0).
- `read_pack(target)` - every file of the target pack with its sha256, and the versions on disk under `runs/<target name>/versions/`; print them. A generation that boots is the one whose checksums match what the last patch wrote.
- `propose(pack, task, target, files, summary, visit=1)` - refuse when this visit already has a proposal (one per visit: `proposals/p<visit>*.json` exists); refuse a file outside the pack's `patches:` globs (this pack's front matter); refuse a patch that changes more than 20 % of the target pack's lines or removes the test-rule line from its `SKILL.md`; `lint_pack` the result against the intent. Write `runs/<pack name>/<task name>/proposals/<id>.json` (`{"id", "visit", "target", "files": {path: text}, "summary", "diff"}`, ids `p001`, `p002`, ...), append `{"event": "propose", "id"}` and print the id and the unified diff. Nothing lands.
- `gate(pack, task, id, seed=0)` - the private gate, for a pack whose front matter says `approval: gate` (or `both`): snapshot the target under `runs/<target name>/versions/gen_NNN/`, land the proposal's files, then `private_score` the proposal's evidence recipe and the incumbent (the best val recipe of the newest problem in the target's log); keep the patch only if the evidence recipe did not score lower, else restore the snapshot. Append `{"event": "gate", "id", "before", "after", "keep", "version"}` and print `decision` (`keep` | `rollback`), the two scores and `landed`. Nobody is asked.
- `private_score(pack, task, recipe, seed=0)` - the recipe fitted on train and scored on the private part of the split; costs no budget and touches no state; refuse for an actor pack (only a meta pack may see the private part, and no arm's `score_test` ever does).
- `rollback(target, version)` - restore every file of the target pack (both mirrors) from `runs/<target name>/versions/<version>/`; append `{"event": "rollback", "version"}` to the newest trace; print the files restored.

## Forbidden

- fit_recipe, score_test, save_model, load_splits - zero fits: the meta pack replays the log and never touches a split but the private one
- write_card, apply - cards are the verifier's; the gate, not the human, lands the policy line
