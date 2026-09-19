# Zero to Hero: Recursive Self-Improvement — a hello world, skills only (outline, v9)

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

## The job: a sequence of simple ML problems, one harness, growing experience

The harness solves **simple ML problems in order**, and what it learned on
problem 1 must make it better at problem 2, then 3 — until the *pack*
(memory, cards, policy line, harness text) is an expert and the *model
weights* are exactly what they were. Each problem is a small tabular or
image-like classification task with a hard budget of **24 `fit()` calls per
arm**, a locked test split scored once, and the same recipe space (scaling,
encoding, model ∈ {logreg, rf, hgb}, one hyper-parameter, class weight) so
that experience can transfer. The curriculum ships in `rsi/tasks/`, one
`task.json` per problem, offline and deterministic:

| # | Problem | Source | Why it is in the sequence |
|--:|---|---|---|
| 1 | Adult Census Income (> 50k) | bundled 6k-row sample (OpenML 1590 / UCI, CC BY 4.0) | mixed numeric + categorical, class imbalance — the first lessons the pack learns (encoding, `class_weight`) |
| 2 | Breast cancer (malignant) | `sklearn.datasets.load_breast_cancer` | all numeric, small — does "scale before logreg" transfer? |
| 3 | Wine (3 classes) | `sklearn.datasets.load_wine` | multiclass: metric becomes macro one-vs-rest ROC-AUC; cards conditioned on `n_classes` |
| 4 | Digits (10 classes) | `sklearn.datasets.load_digits` | 64 numeric features, image-like — tree depth and learning-rate cards get counterexamples |
| 5 | Synthetic shifted table A | `common/synth.py` (seeded) | a table whose profile flips which recipe fields matter — the superstition test |
| 6 | Synthetic shifted table B | `common/synth.py` (seeded) | the same, imbalanced and small |
| 7 | **Exam** | `common/synth.py` (seeded, never used for writing) or Bank Marketing when online | the held-out problem: frozen pack, matched budget, memory arm vs `MEMORY_OFF` arm |

Every problem's `task.json` names the target, the metric (`roc_auc` or
`roc_auc_ovr_macro`), the budget, the allowed models and the **profile** the
verifier may condition on (`n_rows`, `n_features`, `n_classes`, `imbalance`,
`has_categorical`). The learning curve — per problem, memory arm minus
`MEMORY_OFF` arm at the same budget, and wasted fits before the first good
recipe — is the series' headline chart, and the exam problem is its proof.

## What the paper says, and how the lessons are organised around it

*The Last AI Built by Humans: Toward Genuine Recursive Self-Improvement*
(arXiv:2609.11873v2, 15 Sep 2026, 37 authors) is not a catalogue of tricks;
it is a **framework for deciding whether a loop is RSI at all**, and it makes
four moves this series copies.

1. **It measures where RSI would matter.** The Headroom-Closed Index
   normalises benchmark progress per domain (0 = the frontier the year the
   benchmark appeared, 100 = perfect). Bounded domains are nearly closed
   (advanced mathematics 86.4, graduate science 85.8); interactive,
   stateful ones are not (software engineering 52.6, search / terminal
   agents 56.8, tool agents 39.9). So RSI is worth the most exactly where an
   agent must *operate a system with hidden rules* — which is why our job is
   a harness solving a sequence of ML problems, not a static QA benchmark.
2. **It defines RSI by where the authority sits.** The unit of analysis is
   the improvement loop, and autonomy is "which decisions have moved from the
   designer to the system": what to improve (L1), how (L2), which experience
   to acquire (L3), whether to revise persistent state from deployment
   feedback under an external acceptance rule (L4), whether to revise the
   improver / verifier / successor procedure itself (L5). B0 — a better
   answer this turn with no persistent change — is excluded. Every lesson
   below states its rung *and what stays human*.
3. **It sets the evidence bar.** *Structural* recursion (a revised mechanism
   governs a later round) is not enough; *effective* recursion needs
   stronger successors **under comparable budgets and independent
   evaluation**. Three challenges every claim must survive: **safe
   inheritance** (transfer tests, version histories, rollback — Gödel Agent
   lost ground in 14 % of trials), **autonomy attribution** (DGM raised
   SWE-bench 20 → 50 %, but its archive and parent selection stayed
   human-fixed), **reliable verification** (repeated evaluator access
   rewards exploitation — seed cherry-picking and test-label extraction were
   observed; freeze evaluators per epoch, anchor to an independent
   ground truth, match compute). Our budget object, locked test, private
   gate, `versions/` + rollback and the approval cycle are these three
   challenges turned into tools.
4. **It reads industry, not only papers.** Eight deployed loops (Theseus,
   Lark, Xiaohongshu's dual-timescale recommender, Humanlaya, ModelBest,
   Tencent Hunyuan, an agent-native research lab, Frontis.AI) show the
   practical constraints — feedback pipelines, validation infrastructure,
   rollback, human governance — that isolated experiments skip. Our human
   approval cycle and the two-timescale meta-skills lesson come from there.

The paper's honest verdict is the series' thesis: today's public RSI is
mostly L1–L4 with a human acceptance rule; L5 exists in a few systems
(A-Evolve-Training 0.80 → 0.86 over four rounds, Red Queen GM, AIDE²) and is
credible only where the evaluator is protected. "Genuine" RSI would need
closed loops with persistence, transferred and *attributed* autonomy,
verified inheritance under matched budgets, and domain-appropriate feedback
infrastructure. The series never claims more than L5 *flavour*, and says so
in every README.

### Lesson ↔ paper map

| Lesson | Rung | Which decision the system takes | What stays human | Paper section / evidence rule it exercises |
|---|---|---|---|---|
| 00 intent | L1 precondition | none | what to improve, how, success | §3.2: humans specify objective, procedure, acceptance |
| 01 regular · 02 loop · 04 graph | not RSI | none (executes a fixed procedure) | everything | §2.2 distinction from AutoML / agentic systems; §3.1 B0 boundary |
| 03 · 05 meta generates loop / graph | L1 | executes a generation procedure | the spec, the acceptance (`y`/`n`/`edit`) | §3.2 L1; §5 human release gates |
| 06 RSI harness | L4 | revises persistent state (cards) from run feedback | the verifier contract, the off switch | §3.5 L4 (PANDO-style admit / demote rules); Challenge 3 (verifier cannot see the actor) |
| 07 proof | — | — | the test, the exam | §1.7 effective recursion; Challenge 3 protected evaluation, matched budgets |
| 08 meta generates RSI | L1 → L4 | generates a mechanism that will change itself | approving that mechanism | Challenge 2 attribution: the human approves an improver, not a result |
| 09 RSI meta harness | L4 → L5 flavour | revises the improver's policy line; keep-or-rollback | `approval: human`; the gate and the archive rule | §3.6 L5; Challenge 1 rollback + versions; Red Queen GM frozen evaluator |
| 10 Dream-RSI | L2 | chooses the search strategy from replay | the policy library | Table 2: experience replay; §3.3 L2 |
| 11 RSIAgent | L3 + L4 | chooses the next experiment; freezes memory | the verifier | §3.4 L3 exploration; frozen memory at test |
| 12 ModularRSI | L2 → L5 flavour | patches one harness module off-benchmark | module boundaries, the pool | §3.6 harness modules; Challenge 3 benchmark-disjoint validation |
| 13 Recuris | L4 | consolidates skill memory | validation rule | Table 2: memory / skill consolidation |
| 14 DGM lineage | L5 flavour | rewrites its own `SKILL.md` / `loop.json` | archive rule, parent choice, gate | Challenge 2 (the paper's DGM example verbatim) |
| 15 AIDE² | L5 flavour | rewrites the inner agent, keep-if-better | the budget meter, the task set | §1.7 effective recursion across a heterogeneous set; Challenge 3 guards |
| 16 MetaSkill-Evolve | L5 | revises its own meta-skills on a slow clock | the clock, the human `y` on meta changes | §5.3 dual-timescale industry loop; §3.6 |
| 17 map | — | — | — | the ladder, HCI, the three challenges as the acceptance test |

## The definition we use — *The Last AI Built by Humans* (arXiv:2609.11873)
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
`score_test(recipe)` (once, after `FREEZE`), `walk_path` (04), `lint_pack` / `propose` / `decide` / `apply` (03, 05, 08, 09),
`private_score`, `patch_pack`, `rollback` (09), `rank_policies` (10), `contrast` (12). Every tool is a gate:
`fit_recipe` counts the budget and refuses a recipe a `forbid` card rules out;
`score_test` refuses before freeze and on a second call; `write_card` refuses a
card that names test or intent. The skill *says* the rule; the tool *enforces*
it — that is what makes a skill pack testable. `fake.py` — a scripted /
rule-driven fake model for the tests (reads the cards in its prompt and
proposes accordingly), so every claim is provable without a key.

## Format — conforms to the Claude Academy *AI-native SDLC playbook*

The series is laid out like the course (six SDLC stages, one lesson per
step, ~1 hour of reading plus the runs). `rsi/README.md` is the course page:
title, one-line description, **What you'll learn** ("By the end of this
course, you'll be able to …"), **Who this course is for**, **Prerequisites**,
estimated time, and the lesson list grouped by stage. Every step README is a
lesson page with these headings, in this order, verbatim:

1. `# <Lesson title>` then one paragraph of concept (why this lesson exists).
2. `## Getting started` — prerequisites, what the previous lesson left on disk, what this one adds.
3. `## How to execute it` — numbered steps: the exact commands (bash and PowerShell), what to answer at each approval.
4. `## What it looks like` — the pack files shown (front matter first), the expected terminal output from a real run, and the `Files` tree.
5. `## Governance considerations` — who approves what, the off switches, what the model may not do and which tool enforces it, what is and is not self-modified (autonomy attribution).
6. `## How to measure it` — the test claims of this lesson (each one line: claim → the test that proves it), the scorecard fields it reports, and how to run `python run_tests.py rsi`.
7. `## Next lesson` — one line; previous lesson linked too.

| SDLC stage | Lessons (steps) |
|---|---|
| Stage 1: Plan | 00 intent — capture what to improve, how, and what counts as success as `task.json` + `acceptance.md` |
| Stage 2: Design | 01 regular harness · 02 loop engineering · 04 graph engineering with loops |
| Stage 3: Build | 03 meta generates the loop harness · 05 meta generates the graph harness · 06 the RSI harness · 08 meta generates the RSI harness |
| Stage 4: Test | 07 proof — locked test, transfer, the scorecard; `run_tests.py rsi` as the continuous eval |
| Stage 5: Deploy | 09 the RSI meta harness — approval cycles as gates (human, then the private gate), versions and rollback |
| Stage 6: Maintain | 10–14 RSI by method (Dream-RSI, RSIAgent, ModularRSI, Recuris, DGM, AIDE², MetaSkill-Evolve) — closing the loop on the metrics; 15 map |

Skills use the same layout the course teaches (`skills/<name>/SKILL.md` with
front matter naming when it triggers, then the instructions), and every rule a
skill states that must hold absolutely is also enforced by a tool or the
harness — the course's "advisory skill + deterministic gate" split.

## Steps — every step is a skill pack booted by the one harness

The spine (the owner's sequence; the Google doc is a reference for file
shapes, not the plan): **plain harness → loop engineering → a meta skill that
generates the loop harness under human approval → graph engineering with
loops → a meta skill that generates the graph harness under human approval →
a harness with RSI → its proof → a meta skill that generates the RSI harness
under human approval → an RSI meta harness that improves the harness, under
human approval and then under a private gate → RSI by method**. Every
"generate" and every "improve" goes through the same **human approval cycle**:
the meta pack proposes (a whole pack or a diff), the harness shows it and
asks, the human answers `y` / `n` / `edit`, and only then does it land — the
codelab's stage 35 `ask_user` / approve pattern, with a scripted human in the
tests. That cycle is what the framework paper calls the *human acceptance
criteria*; each step says which decisions are the model's and which are the
human's (autonomy attribution).

Pack files use the repo's skill front matter (`name`, `description`,
`metadata: {type, version, rsi}`), so the packs also load in the root
codelab's harness. The approval cycle lives in `common/approve.py`
(`propose(kind, payload) → proposal id`, `decide(id) → y/n/edit`, `apply(id)`)
and every meta pack's `tools.md` names it.

### Part 1 — Harness engineering, no RSI (steps 01–05)

| Step | The pack (what is on disk) | The one idea | Rung |
|-----:|-----|------|------|
| 00 `intent` | `task.json` (what to improve: Adult income > 50k; metric ROC-AUC; budget 24 fits per arm; allowed models; the locked test rule; the transfer table) and `acceptance.md` (the scorecard fields and the pass rule, written *before* any pack exists); `run.py` validates both against `common/task.schema.json` | **Capture the intent first.** Humans specify what should be improved, how, and what counts as success — the framework paper's L1 precondition and the playbook's `intent.md`. Every later pack, writer and verifier reads this file; nothing may widen it. | L1 precondition |
| 01 `regular_harness` | `skills/adult-income-regular/`: `SKILL.md` (boot only this pack; fit the baseline; run the static 24-recipe list in order; pick best val; `score_test` once; `save_model`; stop; "next run boots this same text"), `tools.md` (allowed / forbidden), `schema.json` (task, target, metric, `n_fits: 24`, baseline, the 24 recipes) | A repeatable trainer. Same text every run, same waste every Monday. **The control arm, and not RSI.** The harness, the budget object, the locked test and the append-only trace arrive here. | B0 / AutoML |
| 02 `loop_harness` | `skills/adult-income-loop/`: `SKILL.md`, `loop.json` (`kind: counted_while`, `N: 24`, counter `t`, `error_still_counts`, `body`, `exit: FREEZE → score_test once → save_model`, `illegal: change N, reorder, second while, score_test before FREEZE, write memory.json`), `recipes.json`, `tools.md` + `write_loop_log` (audit only) | **Loop engineering**: name the steps, the counter and the gate in a file; the tools enforce what the file declares. Still not RSI: the log is never read back; generation n+1 loads the same `loop.json`. | harness engineering |
| 03 `meta_generates_loop` | `skills/loop-writer/`: `SKILL.md` ("you do not fit models; given `task.json` write a loop pack: SKILL.md, tools.md, loop.json, recipes.json; then `propose` it and wait"), `tools.md` (`read_task`, `lint_pack` (the generated pack must boot in a dry run), `propose`, `apply` — never `fit_recipe`), `task.json` (target, metric, budget, allowed models) | **A meta harness whose output is a loop harness, under human approval.** The human sees the whole proposed pack, answers `y` / `n` / `edit`; `n` means nothing lands. One shot from a spec: generating twice yields the same proposal, and running the generated pack never changes it. Most "agent builds agent" demos stop here — not RSI yet. | L1: humans specify what / how / success; AI executes; human accepts |
| 04 `graph_harness` | `skills/adult-income-graph/`: `SKILL.md`, `graph.json` (nodes = legal operators; edges = hard dependencies; `score_test` a sink with `gate: freeze_only`; constraints: one encode / one scale / one model per path, no cycles), `paths.json` (baseline + 24 static paths with bindings), `loop.json` (the counted while now iterates over paths), `tools.md` + `walk_path(path_id)`; illegal path = skip and count, never invent | **Graph engineering with loops**: the job is a DAG, a recipe is a path, the loop walks paths. `graph.json` and `paths.json` are `mutable: false`. Still not RSI. | harness engineering |
| 05 `meta_generates_graph` | `skills/graph-writer/`: step 03's writer extended to emit `graph.json` + `paths.json` + `loop.json`; `lint_pack` now checks the DAG (no cycles, constraints, every path legal); the proposal shows the graph as a node/edge list and the human approves, edits (e.g. removes an edge) or rejects | **A meta harness that generates a graph harness, under human approval.** `edit` is the interesting answer: the human's change is what lands, and the writer never sees the run results — still no feedback loop, still not RSI. | L1 |

### Part 2 — The first RSI, its proof, and the meta harnesses that make and improve it (steps 06–09)

| Step | The pack | The one idea | Rung |
|-----:|-----|------|------|
| 06 `rsi_harness` | `skills/adult-income/` (inner H): `SKILL.md` (boot order incl. `memory.json` unless `MEMORY_OFF` and `traces.jsonl`; for t in 1..24 read cards, propose ONE recipe from the schema, fit, append; FREEZE; `score_test` once; "only a meta pack may patch this pack"), `memory.json` (`[]`), `memory.schema.json` (`if` profile predicate → `then` prefer/forbid one field value, `evidence`, `counter`), `tools.md` + `read_memory`; `skills/adult-income-verifier/` (input `{recipe, val_auc, error, profile}` only; IF/THEN cards with evidence and counterexample; refuse cards that mention test or intent; tools `read_traces`, `write_card`) | **The first RSI file.** A card is a constraint on the *next* proposal (`fit_recipe` refuses a forbidden recipe), and no one grades their own homework: the verifier pack boots with only the log. `MEMORY_OFF` is the off switch: same 24 fits, the numbers must fall back. | L4: deployment feedback revises persistent state under our acceptance rule |
| 07 `proof` | `eval.md` in the inner pack (24 vs 24 with `MEMORY_OFF`, the delete-file check, the scorecard fields, "test touched before freeze: no"); `run.py --curriculum` runs problems 1→6 in order, carrying the pack forward, and prints the **learning curve** (per problem: memory arm − `MEMORY_OFF` arm at the same budget, wasted fits, cards added/demoted); `run.py --exam` boots the frozen pack on problem 7 | Locked test = you did not peek. The curve = experience from problem n helped on n+1: structural recursion you can see. The exam = effective recursion under a matched budget and an independent evaluation. The scorecard and the curve are the deliverables of every later step too. | evidence standard |
| 08 `meta_generates_rsi` | `skills/rsi-writer/`: step 05's writer extended to emit the inner pack **and** the verifier pack, `memory.schema.json` and `eval.md` from `task.json`; the proposal shows the verifier contract explicitly and the human must approve it (it is the acceptance rule) | **A meta harness that generates the RSI harness, under human approval.** The human is approving a *mechanism that will change itself later*, not a one-off pack — the README says so and shows the diff the human sees. | L1 for the generation; what it generates runs at L4 |
| 09 `rsi_meta_harness` | `skills/adult-income-meta/` (MH): reads traces + memory + inner pack; writes **one** proposal per visit — new cards, a small `schema.json` forbid, or the search-policy line; size cap 20 %; no `score_test`; `versions/` per generation; `private_score` on a split the inner pack never sees. Two modes on disk: `approval: human` (every generation's patch goes through the human cycle) and `approval: gate` (the private gate decides keep-or-rollback and the human only sees the log). `run.py` boots inner (problem n) → meta → inner (problem n+1) across the whole curriculum, one generation per problem; `META_OFF` | **The RSI meta harness that improves the harness — problem by problem.** Problem 1 teaches the pack encoding and class weights, problem 3 teaches it multiclass metrics, problem 5 demotes a superstition; by the exam the pack is the expert and the model is unchanged. Generation n+1 is RSI only if it boots what generation n wrote; the reboot is the recursion. Under `approval: human` the human is the acceptance rule (L4); under `approval: gate` the system revises its own improver's policy line behind a protected evaluator (L5 flavour). The archive rule and the gate itself stay human — say so. Rollback and version history are safe inheritance made concrete. | L4 → L5 flavour, switchable in one line |

### Part 3 — RSI by method, one published system per step, same curriculum (steps 10–16)

Each step is a variant of the step 06/09 packs plus at most one new tool, so
`diff -r` between two methods shows exactly what the method changes. Every
method step reports the step 07 scorecard (matched budget, one test score,
transfer), runs under the step 09 approval cycle, and says which file improved.

| Step | Method (paper) | The pack | What improves / the one idea |
|-----:|-----|------|------|
| 10 `rsi_dream` | Dream-RSI (arXiv:2609.14858) | `policies.md` (random, neighbours-of-top-3, prefer-untried-family, obey-memory); tool `rank_policies(names)`: replays `traces.jsonl` as a simulator, scores each policy best-of-first-k over the *logged* recipes with zero fits, unvisited picks = "unknown"; the meta pack proposes the winner as the inner **search-policy line**; the next online lap grows the log | **The search policy.** History is an exact gym for the recipes you visited and silent elsewhere; recursion pays only if the next lap visits new places (saturation shown, not hidden). |
| 11 `rsi_agent` | RSIAgent (arXiv:2609.15364) | three packs: `curriculum` (picks the next experiment by uncertainty `u = (1−success) + c/(n+1)`, broad phase large `c`, deep phase small `c` + fault rate), `actor` (proposes and runs), `verifier` (sees only the world result); memory frozen before `score_test` and reused on the transfer table | **The memory, chosen on purpose.** Broad-then-deep spends the same fits on higher-information experiments; frozen memory at test is what makes the comparison fair. |
| 12 `rsi_modular` | ModularRSI (arXiv:2609.14857) | the inner pack split into five files that mirror the paper's modules (`agent_loop.md`, `tool_use.md`, `observation.md`, `context.md`, `completion.md`); a disjoint pool of synthetic tables (`pool/`, never the eval table); tool `contrast(pool_traces)` pairs a success and a failure on the same task and names the module; the meta pack proposes a patch to **one module**, validates on the pool, then integrates; transfer shown across two fake actors | **A harness module, evolved off the benchmark.** Contrast localises the bug to a module; the benchmark-disjoint pool kills leaderboard overfitting; a patch that helps both actors improved the workshop, not one model's quirks. |
| 13 `rsi_skill_memory` | Recuris (arXiv:2608.24876) | memory as a **skill package**: `skill-memory/manifest.yaml` + markdown skill cards (one per situation), a small `working.md` the actor rewrites per run ("what I am doing, which cards apply"); the meta agent turns execution evidence into localised, validated card updates; gains reported by horizon | **Experiential + working memory.** Skill selection is grounded in current need, not the whole history; the memory is git-native (files you can diff). |
| 14 `rsi_self_modifying` | Darwin Gödel Machine lineage (DGM, arXiv:2505.22954; Mendel / Huxley GM as reading) | the meta pack may propose rewrites of the inner pack's **`SKILL.md` and `loop.json` themselves** (the harness source), keeping an `archive/` of variants with their held-out scores and choosing parents from the archive, one generation deep, behind the private gate and the human cycle | **The agent's own source.** The empirical Gödel machine: keep an archive of stepping stones, expand promising ones; the archive rule and the gate stay human — say what is and is not self-modified. |

| 15 `rsi_aide2` | AIDE² (Weco AI, July 2026; tech report announced, code not released) | inner loop = the step 06 pack as an AIDE-style **tree search over solutions** with three operators (`draft`, `debug`, `improve`) and an eval reviewer that extracts the score from the run; outer loop = a meta pack that **rewrites the inner pack's operator text** and keeps the rewrite only if it beats the previous best **across the whole heterogeneous curriculum under a fixed cost budget** (fits and tokens, metered by the harness); three reward-hacking guards the outer loop must keep: an anti-overfitting line in every operator prompt, a hard guard that re-runs a suspicious score, a statistical layer that discards outlier successes | **Autoresearch on autoresearch.** Keep-if-better across many problems under one budget is what turns "a better run" into "a better researcher"; the guards are why the score means something. Reported: seven successive improved versions in 100 outer steps, 16× context compression — *reported, unverified* until the report and AIDE85 are released. |
| 16 `rsi_meta_skills` | MetaSkill-Evolve (arXiv:2607.05297) | two timescales on one frozen model: **task skills** (the inner pack's cards and policy line) evolve every problem; **meta-skills** (the meta pack's own five roles as files — `analyzer.md`, `retriever.md`, `allocator.md`, `proposer.md`, `evolver.md`) evolve every k problems by the same pipeline, with no extra model or objective; the human cycle approves meta-skill changes, the private gate approves task-skill changes | **The improver's skills improve too — slowly.** This is the "and so on": the pack that patches the pack is itself a pack with a version history, and its changes are rarer and gated harder. |

### Part 4 — Map (step 17)

| Step | Adds | The one idea |
|-----:|------|--------------|
| 17 `map` | README + `run.py` that prints the ladder with steps 01–16 placed; the learning curve of every method on the same curriculum side by side; the file-by-file table (regular vs loop vs graph vs generated vs RSI vs each method, and who approved what); ScienceBuddy (arXiv:2609.17523, harness then weights, reading only) and OpenAI's stated priority as the rungs this series refuses to touch; the terminology table (self-refine, learning, self-organise/emergence, AutoML, bounded, genuine); the acceptance test; every external number marked *reported* with its source | You recognise the nouns because you built the toy — and you can point at which file each method changed and who approved it. |

Eighteen small steps. Everything runs offline in tests with the fake model and
a scripted human; `python run.py` in a step needs a key like the rest of the
repo, and asks you at every approval.

## What each test proves (offline, fake model, scripted human, no key)

- 00: `task.json` and `acceptance.md` validate against the schema; a pack that tries to raise the budget or touch the test rule is rejected by `lint_pack`; the acceptance fields are exactly the scorecard fields every later step reports.
- 01: the fake model follows `SKILL.md` (24 fits in schema order, best-val pick, one `score_test`); the 25th `fit_recipe` and the second `score_test` are `Error:` results; an unknown / disallowed / malformed tool call is an `Error:` result and the loop continues; the trace is append-only; the same pack twice gives the same log.
- 02: `loop.json` is honoured by the tools (25th fit, pre-FREEZE `score_test`); the audit log is never read back; the pack is byte-identical after a run.
- 03: the writer cannot call `fit_recipe` (not in its `tools.md` → `Error:`); the proposal is shown before anything lands; scripted `n` leaves the disk untouched, `y` lands exactly the proposal, `edit` lands the human's text; generating twice from the same `task.json` gives byte-identical proposals; the generated pack boots and passes step 02's checks; running it changes none of its files.
- 04: an illegal path is skipped and counted, never replaced; `score_test` is unreachable before FREEZE; `graph.json` / `paths.json` byte-identical after a run; the loop iterates paths in order.
- 05: `lint_pack` rejects a proposal with a cycle or a path that violates a constraint before the human ever sees it; an `edit` that removes an edge lands and the pack still boots.
- 06: the verifier pack's transcript contains no actor text; `write_card` refuses a card mentioning `test` or intent; a planted wrong card is demoted after k counterexamples; `fit_recipe` refuses a forbidden recipe; with the rule-driven fake model, same seeds and budget, the memory arm ≥ the `MEMORY_OFF` arm and wastes fewer fits; `MEMORY_OFF` reproduces step 01's numbers exactly.
- 07: test scored exactly once per problem; all scorecard fields present; running problems 1→6 carries the pack forward and the learning-curve gap (memory − `MEMORY_OFF`) is ≥ 0 on every problem and larger on problem 6 than on problem 2 for the rule-driven fake model; on the exam problem the frozen pack beats `MEMORY_OFF` on ≥ 3 of 5 seeds and the report names a card that did not transfer.
- 08: the proposal contains the verifier contract verbatim and is refused by `lint_pack` when it is missing; the generated packs pass step 06's tests; scripted `n` lands nothing.
- 09: generation n+1 boots the files generation n wrote (checksums in the trace); under `approval: human` no patch lands without a `y` and an `edit` lands the human's version; under `approval: gate` a patch that raises val and lowers `private_score` is rejected and `versions/` restores the previous pack; `META_OFF` leaves the pack byte-identical; the meta pack cannot call `score_test`.
- 10: `rank_policies` makes zero fits (the budget counter proves it); a policy preferring unvisited recipes scores "unknown"; the winner is proposed as the search-policy line and the next lap adds new recipes to the log.
- 11: the broad phase touches every family before the deep phase repeats one; the deep phase prefers the family with the most faults; memory is frozen before `score_test` and unchanged on the transfer table.
- 12: `contrast` names the module whose text differs between the success and the failure; the patch touches exactly one module file; validation runs on the pool, never the eval table; the patched module helps both fake actors.
- 13: a skill card is selected by the working-memory need, not by recency; an update is localised to one card and validated before it lands; the horizon report shows the gain per sequence length.
- 15: the outer loop's keep-if-better is evaluated across every problem of the curriculum under one metered budget (asserted from the trace); a rewrite that wins on one problem and loses on the set is rejected; the three guards are present in every operator prompt and a suspicious score is re-run (scripted).
- 16: task skills change every problem, meta-skills only every k problems (counted); a meta-skill change never lands without the human `y`; the meta pack's version history is a file you can diff.
- 14: the archive holds every variant with its held-out score; the parent is chosen from the archive, not always the latest; a rewrite that lowers the private score never becomes a parent; `SKILL.md` and `loop.json` are the only self-modified files (asserted).
- All: `python run_tests.py rsi` and `python check_snippets.py rsi` green.

## Validation of the source tutorial against the papers (18 Sep 2026)

Repos and abstracts checked: RSIAgent (arXiv:2609.15364, AetherLabsAI/RSIAgent), Dream-RSI (2609.14858, code "being prepared"), ModularRSI (2609.14857; modules are Agent Loop, Tool Use, Observation Management, Context Management, Task Completion Detection — not "verification"), ScienceBuddy (2609.17523, inner harness loop + outer RL loop), Recuris (2608.24876, +32.2 on the longest tasks), the framework paper (2609.11873) and the July corpus survey (2607.07663). The tutorial's descriptions match; its specific numbers (162×, 71.97→78.98, 47.57→52.43, 8×A100, gpt-6-astra as improver) are not in the abstracts and stay *reported*. Conceptual corrections the series makes: "bounded vs strong" is too coarse (use the rungs + structural/effective); the locked test split is the wrong hero test (transfer table); free-text cards are not executable (typed cards + tool enforcement); a verifier that sees only `{recipe, val_auc, error}` cannot write the cards shown (it also gets the profile); single-seed "delete the file" claims are noise (paired seeds, matched budget); "replay each policy on the log" is under-specified (rank logged recipes, unvisited = unknown); no rollback anywhere (versions + private gate).

## Repo wiring

`rsi/README.md` (series codelab, top-down); `run_tests.py` / `check_snippets.py` already know `rsi/step_*`; `rsi/data/` bundled sample + licence note; `rsi/common/` harness, tools, fake model, loader, synth; `scikit-learn`, `pandas`, `numpy` in `requirements.txt`.
