# Zero to Hero: Recursive Self-Improvement — a hello world, skills only (outline, v5)

**The skill pack gets smarter. The model weights do not. You can measure both, turn it off, and roll it back.**

Hello world, concept first, **skills-based from the first step**: the agent is
configured by files it boots (`SKILL.md` and its siblings), never by Python
that drives the loop. Python only supplies the *tools* a skill names
(`fit_recipe`, `write_card`, `score_test` …) and one tiny skills harness that
boots a pack and runs the model loop — the same shape as the root codelab's
stage 4 (skills) + stage 15 (`execute()` as the one place every tool call goes
through). Every step adds one idea by changing the files, so `diff -r` between
two steps shows exactly what became RSI. Every step runs offline in tests with
a fake model; `python run.py` needs `BASE_URL` / `API_KEY` / `MODEL` like the
rest of the repo.

## The job (real software, no toy factory)

Improve a tabular classifier on **Adult Census Income** under a hard budget of
**24 `fit()` calls per arm**, then prove the *pack* improved, not just the
model: freeze the memory and run the same budget on a **shifted synthetic
table** it never saw. Bundled 6k-row Adult sample (offline), OpenML cache when
online. Models: `LogisticRegression`, `RandomForest`, `HistGradientBoosting`.
Metric: ROC-AUC on validation during search; the test split is scored **once**,
after freeze, by a tool that raises on a second call.

## The definition we use — *The Last AI Built by Humans* (arXiv:2609.11873)

RSI: "an autonomous, closed-loop process in which an AI system identifies its
own limitations, develops and validates improvements, and uses the resulting
capabilities to improve the improvement process itself." Persistent changes
across rounds that affect how later improvements are generated, evaluated,
selected or consolidated. Not RSI: B0 ("output change without persistent
system change"), AutoML / continual learning with designer-fixed objective,
search space and acceptance test. **Structural** recursion (a revised mechanism
governs a later round) vs **effective** recursion (stronger successors under
comparable budgets and independent evaluation). Three problems every claim
must answer: **safe inheritance** (transfer tests, version histories,
rollback), **autonomy attribution** (AI-controlled decisions vs fixed
procedure vs human acceptance), **reliable verification** (protected
evaluation, matched budgets). Rungs: L1 execute → L2 choose strategy → L3
choose experience → L4 revise state under an external acceptance rule → L5
revise the improver itself. Every step names its rung and what stays human.

## The one harness (built once, in `rsi/common/`, ~200 lines, never a step)

`harness.py` — `boot(pack_dir)` reads `SKILL.md` (becomes the system prompt),
`tools.md` (which tools this pack may call — the allowed set), `schema.json`
(the recipe space, given to the model verbatim) and, when present,
`memory.json` (cards, appended to the prompt unless `MEMORY_OFF`). Then the
loop from stage 15: call the model, run every tool call through `execute()`
(unknown / disallowed / malformed → `Error:` result, never a crash), append,
repeat, stop when the pack's budget is spent or the model answers in text.
`tools.py` — the tool table: `load_splits`, `fit_recipe(recipe)`,
`read_memory`, `write_card(card)` (verifier only), `read_traces`,
`score_test(recipe)` (once, after `FREEZE`), `rank_policies(names)` (step 07),
`private_score`, `patch_pack`, `rollback` (step 06), `walk_path` (02),
`write_pack` / `boot_pack` (03), `contrast` (09). Every tool is a gate:
`fit_recipe` counts the budget and refuses a recipe a `forbid` card rules out;
`score_test` refuses before freeze and on a second call; `write_card` refuses a
card that names test or intent. The skill *says* the rule; the tool *enforces*
it — that is what makes a skill pack testable. `fake.py` — a scripted /
rule-driven fake model for the tests (reads the cards in its prompt and
proposes accordingly), so every claim is provable without a key.

## Steps — every step is a skill pack booted by the one harness

The spine (the owner's sequence; the Google doc is a reference for file
shapes, not the plan): **plain harness → loop engineering → graph engineering
with loops → a meta harness that generates a harness → a harness with RSI →
a meta harness that generates the RSI harness → RSI by method** (Dream-RSI,
RSIAgent, ModularRSI, Recuris, DGM; ScienceBuddy as reading). Three parts:
harness engineering that is *not* RSI, the first RSI and its proof, then one
published method per step on the same job so they can be compared file by
file. Pack files use the repo's skill front matter (`name`, `description`,
`metadata: {type, version, rsi}`), so the packs also load in the root
codelab's harness.

### Part 1 — Harness engineering, no RSI (steps 00–03)

| Step | The pack (what is on disk) | The one idea | Rung |
|-----:|-----|------|------|
| 00 `regular_harness` | `skills/adult-income-regular/`: `SKILL.md` (boot only this pack; fit the baseline; run the static 24-recipe list in order; pick best val; `score_test` once; `save_model`; stop; "next run boots this same text"), `tools.md` (allowed / forbidden lists), `schema.json` (task, target, metric, `n_fits: 24`, baseline, the 24 recipes) | A repeatable trainer. Same text every run, same waste every Monday. **The control arm, and not RSI.** The harness, the budget object, the locked test and the append-only trace arrive here. | B0 / AutoML |
| 01 `loop_harness` | `skills/adult-income-loop/`: `SKILL.md`, `loop.json` (`kind: counted_while`, `N: 24`, counter `t`, `error_still_counts`, `body`, `exit: FREEZE → score_test once → save_model`, `illegal: change N, reorder, second while, score_test before FREEZE, write memory.json`), `recipes.json`, `tools.md` + `write_loop_log` (audit only) | **Loop engineering**: name the steps, the counter and the gate in a file; the tools enforce what the file declares. Still not RSI: the log is never read back; generation n+1 loads the same `loop.json`. | harness engineering |
| 02 `graph_harness` | `skills/adult-income-graph/`: `SKILL.md`, `graph.json` (nodes = legal operators; edges = hard dependencies; `score_test` a sink with `gate: freeze_only`; constraints: one encode / one scale / one model per path, no cycles), `paths.json` (baseline + 24 static paths with bindings), `loop.json` (the counted while now iterates over paths), `tools.md` + `walk_path(path_id)`; illegal path = skip and count, never invent | **Graph engineering with loops**: the job is a DAG, a recipe is a path, the loop walks paths. `graph.json` and `paths.json` are `mutable: false`. Still not RSI. | harness engineering |
| 03 `meta_generates_harness` | `skills/harness-writer/`: `SKILL.md` ("you do not fit models; given `task.json` write a pack: SKILL.md, tools.md, schema.json, loop.json"), `tools.md` (`read_task`, `write_pack`, `boot_pack` (dry run: the generated pack must boot and pass the harness's lint), `task.json` (target, metric, budget, allowed models); the generated pack is step 01's shape | **A meta harness whose output is a harness.** One shot, from a spec, no run feedback: generating twice from the same spec yields the same pack, and running the pack never changes it. This is where most "agent builds agent" demos stop — and it is not RSI yet (nothing persists across rounds that changes the next round). | L1: humans specify what/how/success; AI executes |

### Part 2 — The first RSI, its proof, and the meta harness that makes it (steps 04–06)

| Step | The pack | The one idea | Rung |
|-----:|-----|------|------|
| 04 `rsi_harness` | `skills/adult-income/` (inner H): `SKILL.md` (boot order incl. `memory.json` unless `MEMORY_OFF` and `traces.jsonl`; for t in 1..24 read cards, propose ONE recipe from the schema, fit, append; FREEZE; `score_test` once; "only a meta pack may patch this pack"), `memory.json` (`[]`), `memory.schema.json` (`if` profile predicate → `then` prefer/forbid one field value, `evidence`, `counter`), `tools.md` + `read_memory`; `skills/adult-income-verifier/` (input `{recipe, val_auc, error, profile}` only; IF/THEN cards with evidence and counterexample; refuse cards that mention test or intent; tools `read_traces`, `write_card`) | **The first RSI file.** A card is a constraint on the *next* proposal (`fit_recipe` refuses a forbidden recipe), and no one grades their own homework: the verifier pack boots with only the log. `MEMORY_OFF` is the off switch: same 24 fits, the numbers must fall back. | L4: deployment feedback revises persistent state under our acceptance rule |
| 05 `proof` | `eval.md` in the inner pack (24 vs 24 with `MEMORY_OFF`, the delete-file check, the scorecard fields, "test touched before freeze: no"); `run.py --transfer` boots the frozen pack on the shifted synthetic table | Locked test = you did not peek. Shifted table = the *pack* got better: effective recursion. The scorecard is the deliverable of every later step too. | evidence standard |
| 06 `meta_generates_rsi_harness` | `skills/rsi-harness-writer/` (step 03's writer plus RSI parts: it emits the inner pack, the verifier pack, `memory.schema.json`, `eval.md`) and `skills/adult-income-meta/` (MH: reads traces + memory + inner pack; writes **one** patch per visit — cards, a `schema.json` forbid, or the search-policy line; size cap 20 %; no `score_test`; `versions/` per generation; `private_score` on a split the inner pack never sees decides keep-or-rollback); `run.py` boots writer → inner → meta → inner (generation n+1); `META_OFF` | **A meta harness that generates the RSI harness and then keeps it honest.** Generation n+1 is RSI only if it boots what generation n wrote — the reboot is the recursion. The private gate and the rollback are reliable verification and safe inheritance made concrete; the archive rule and the gate stay human (autonomy attribution). | L5 flavour |

### Part 3 — RSI by method, one published system per step, same job (steps 07–11)

Each step is a variant of the step 04/06 packs plus at most one new tool, so
`diff -r` between two methods shows exactly what the method changes. Every
method step reports the step 05 scorecard (matched budget, one test score,
transfer) so the methods are comparable, and says which file improved.

| Step | Method (paper) | The pack | What improves / the one idea |
|-----:|-----|------|------|
| 07 `rsi_dream` | Dream-RSI (arXiv:2609.14858) | `policies.md` (random, neighbours-of-top-3, prefer-untried-family, obey-memory); tool `rank_policies(names)`: replays `traces.jsonl` as a simulator, scores each policy best-of-first-k over the *logged* recipes with zero fits, unvisited picks = "unknown"; the meta pack patches the inner **search-policy line** to the winner; the next online lap grows the log | **The search policy.** History is an exact gym for the recipes you visited and silent elsewhere; recursion pays only if the next lap visits new places (saturation shown, not hidden). |
| 08 `rsi_agent` | RSIAgent (arXiv:2609.15364) | three packs: `curriculum` (picks the next experiment by uncertainty `u = (1−success) + c/(n+1)`, broad phase large `c`, deep phase small `c` + fault rate), `actor` (proposes and runs), `verifier` (sees only the world result); memory frozen before `score_test` and reused on the transfer table | **The memory, chosen on purpose.** Broad-then-deep spends the same fits on higher-information experiments; frozen memory at test is what makes the comparison fair. |
| 09 `rsi_modular` | ModularRSI (arXiv:2609.14857) | the inner pack split into five files that mirror the paper's modules (`agent_loop.md`, `tool_use.md`, `observation.md`, `context.md`, `completion.md`); a disjoint pool of synthetic tables (`pool/`, never the eval table); tool `contrast(pool_traces)` pairs a success and a failure on the same task and names the module; the meta pack patches **one module**, validates on the pool, then integrates; transfer shown across two fake actors | **A harness module, evolved off the benchmark.** Contrast localises the bug to a module; the benchmark-disjoint pool kills leaderboard overfitting; a patch that helps both actors improved the workshop, not one model's quirks. |
| 10 `rsi_skill_memory` | Recuris (arXiv:2608.24876) | memory as a **skill package**: `skill-memory/manifest.yaml` + markdown skill cards (one per situation), a small `working.md` the actor rewrites per run ("what I am doing, which cards apply"); the meta agent turns execution evidence into localised, validated card updates; gains reported by horizon (short vs long recipe sequences) | **Experiential + working memory.** Skill selection is grounded in current need, not the whole history; the memory is git-native (files you can diff). |
| 11 `rsi_self_modifying` | Darwin Gödel Machine lineage (DGM, arXiv:2505.22954; Mendel/Huxley GM as reading) | the meta pack may rewrite the inner pack's **`SKILL.md` and `loop.json` themselves** (the harness source), keeping an `archive/` of variants with their held-out scores and choosing parents from the archive, one generation deep, behind the private gate | **The agent's own source.** The empirical Gödel machine: keep an archive of stepping stones, expand promising ones; the archive rule and the gate stay human — say what is and is not self-modified (autonomy attribution). |

### Part 4 — Map (step 12)

| Step | Adds | The one idea |
|-----:|------|--------------|
| 12 `map` | README + `run.py` that prints the ladder with steps 00–11 placed; the file-by-file table (regular vs loop vs graph vs generated vs RSI vs each method); ScienceBuddy (arXiv:2609.17523, harness then weights, reading only) and OpenAI's stated priority as the rungs this series refuses to touch; the terminology table (self-refine, learning, self-organise/emergence, AutoML, bounded, genuine); the acceptance test; every external number marked *reported* with its source | You recognise the nouns because you built the toy — and you can point at which file each method changed. |

Thirteen steps, small ones: each Part 3 step is one or two packs and one tool
on top of steps 04–06. Everything runs offline in tests with the fake model;
`python run.py` in a step needs a key like the rest of the repo.

## What each test proves (offline, fake model, no key)

- 00: the fake model follows `SKILL.md` (24 fits in schema order, best-val pick, one `score_test`); the 25th `fit_recipe` and the second `score_test` are `Error:` results; an unknown / disallowed / malformed tool call is an `Error:` result and the loop continues; the trace is append-only; the same pack twice gives the same log.
- 01: `loop.json` is honoured by the tools (25th fit, pre-FREEZE `score_test`); the audit log is never read back; the pack is byte-identical after a run.
- 02: an illegal path is skipped and counted, never replaced; `score_test` is unreachable before FREEZE; `graph.json` / `paths.json` byte-identical after a run; the loop iterates paths in order.
- 03: the generated pack boots and passes the harness lint; generating twice from the same `task.json` is byte-identical; running the generated pack changes none of its files.
- 04: the verifier pack's transcript contains no actor text; `write_card` refuses a card mentioning `test` or intent; a planted wrong card is demoted after k counterexamples; `fit_recipe` refuses a forbidden recipe; with the rule-driven fake model, same seeds and budget, the memory arm ≥ the `MEMORY_OFF` arm and wastes fewer fits; `MEMORY_OFF` reproduces step 00's numbers exactly.
- 05: test scored exactly once; all scorecard fields present; on the shifted table the frozen pack beats `MEMORY_OFF` on ≥ 3 of 5 seeds and the report names a card that did not transfer.
- 06: the writer emits a pack that passes step 04's tests; generation n+1 boots the files generation n wrote (checksums in the trace); a patch that raises val and lowers `private_score` is rejected and `versions/` restores the previous pack; `META_OFF` leaves the pack byte-identical; the meta pack cannot call `score_test`.
- 07: `rank_policies` makes zero fits (the budget counter proves it); a policy preferring unvisited recipes scores "unknown"; the winner is written into the search-policy line and the next lap adds new recipes to the log.
- 08: the curriculum's broad phase touches every family before the deep phase repeats one; deep phase prefers the family with the most faults; memory is frozen before `score_test` and unchanged on the transfer table.
- 09: `contrast` names the module whose text differs between the success and the failure; the patch touches exactly one module file; validation runs on the pool, never the eval table; the patched module helps both fake actors.
- 10: a skill card is selected by the working-memory need, not by recency; an update is localised to one card and validated before it lands; the horizon report shows the gain per sequence length.
- 11: the archive holds every variant with its held-out score; the parent is chosen from the archive, not always the latest; a rewrite that lowers the private score never becomes a parent; `SKILL.md` and `loop.json` are the only self-modified files (asserted).
- All: `python run_tests.py rsi` and `python check_snippets.py rsi` green.

## Validation of the source tutorial against the papers (18 Sep 2026)

Repos and abstracts checked: RSIAgent (arXiv:2609.15364, AetherLabsAI/RSIAgent), Dream-RSI (2609.14858, code "being prepared"), ModularRSI (2609.14857; modules are Agent Loop, Tool Use, Observation Management, Context Management, Task Completion Detection — not "verification"), ScienceBuddy (2609.17523, inner harness loop + outer RL loop), Recuris (2608.24876, +32.2 on the longest tasks), the framework paper (2609.11873) and the July corpus survey (2607.07663). The tutorial's descriptions match; its specific numbers (162×, 71.97→78.98, 47.57→52.43, 8×A100, gpt-6-astra as improver) are not in the abstracts and stay *reported*. Conceptual corrections the series makes: "bounded vs strong" is too coarse (use the rungs + structural/effective); the locked test split is the wrong hero test (transfer table); free-text cards are not executable (typed cards + tool enforcement); a verifier that sees only `{recipe, val_auc, error}` cannot write the cards shown (it also gets the profile); single-seed "delete the file" claims are noise (paired seeds, matched budget); "replay each policy on the log" is under-specified (rank logged recipes, unvisited = unknown); no rollback anywhere (versions + private gate).

## Repo wiring

`rsi/README.md` (series codelab, top-down); `run_tests.py` / `check_snippets.py` already know `rsi/step_*`; `rsi/data/` bundled sample + licence note; `rsi/common/` harness, tools, fake model, loader, synth; `scikit-learn`, `pandas`, `numpy` in `requirements.txt`.
