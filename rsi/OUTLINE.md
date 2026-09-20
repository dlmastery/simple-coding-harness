# Zero to Hero: Recursive Self-Improvement — a hello world, skills only (outline, v11: pure skills, no Python shipped)

**The skill pack gets smarter. The model weights do not. You can measure both, turn it off, and roll it back.**

Hello world, concept first, **skills-based from the first step, run inside a
coding agent, and nothing but skills**: every lesson is a skill pack under
`rsi/step_NN/.claude/skills/` (mirrored to `.agents/skills/`) that you run by
opening Claude Code — or this repo's harness, Antigravity, Codex — in the
lesson directory and typing the prompt its README gives. There is no Python
driver and no tool script: the series ships no `.py` under `rsi/` except each
lesson's `test_step.py`. Everything a tool used to do is a **contract** in the
pack's `tools.md` — inputs, outputs, the file it appends to, the refusals it
must implement — and the agent writes the helper that implements it, on first
use, under `runs/<pack>/helpers/`, with its own Read / Write / Bash tools,
including the scikit-learn fit. The agent IS the harness; the skill pack IS the
program. Every step adds one idea by changing the files, so `diff -r` between
two steps shows exactly what became RSI. Every contract claim is checked
offline (`python run_tests.py rsi`: the pack contract and the lesson's own
claims about its files); the recorded `claude -p` transcripts on every README
are the `RSI_LIVE=1` tests' runs.

## The job: a sequence of simple ML problems, one harness, growing experience

The harness solves **simple ML problems in order**, and what it learned on
problem 1 must make it better at problem 2, then 3 — until the *pack*
(memory, cards, policy line, harness text) is an expert and the *model
weights* are exactly what they were. Each problem is a small tabular or
image-like classification task with a hard budget of **24 `fit()` calls per
arm**, a locked test split scored once, and the same recipe space (scaling,
encoding, model ∈ {logreg, rf, hgb}, one hyper-parameter, class weight) so
that experience can transfer. The curriculum ships in `rsi/tasks/`, one
`NN_<name>/intent.md` per problem (the playbook's Stage 1 artifact: YAML front
matter with the machine-checkable facts, then prose), offline and deterministic:

| # | Problem | Source | Why it is in the sequence |
|--:|---|---|---|
| 1 | Adult Census Income (> 50k) | bundled 6k-row sample (OpenML 1590 / UCI, CC BY 4.0) | mixed numeric + categorical, class imbalance — the first lessons the pack learns (encoding, `class_weight`) |
| 2 | Breast cancer (malignant) | `sklearn.datasets.load_breast_cancer` | all numeric, small — does "scale before logreg" transfer? |
| 3 | Wine (3 classes) | `sklearn.datasets.load_wine` | multiclass: metric becomes macro one-vs-rest ROC-AUC; cards conditioned on `n_classes` |
| 4 | Digits (10 classes) | `sklearn.datasets.load_digits` | 64 numeric features, image-like — tree depth and learning-rate cards get counterexamples |
| 5 | Synthetic shifted table A | seeded `make_classification` parameters in its `intent.md` (one cluster per class) | a table whose profile flips which recipe fields matter — the superstition test |
| 6 | Synthetic shifted table B | seeded `make_classification` (three clusters per class, imbalanced, small) | the same, imbalanced and small |
| 7 | **Exam** | seeded `make_classification` (never used for writing) | the held-out problem: frozen pack, matched budget, memory arm vs `MEMORY_OFF` arm |

Every problem's `intent.md` names the target, the metric (`roc_auc` or
`roc_auc_ovr_macro`), the budget (`budget_fits: 24`), the allowed models, the
data source, the test rule (`test: locked, scored once after FREEZE`) and the
**profile** the verifier may condition on (`n_rows`, `n_features`, `n_classes`, `imbalance`,
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

## The one runtime (a contract, stated in every pack's `tools.md`, built by the agent, never shipped)

There is no model loop in Python and no tool script. A lesson is run by a
coding agent that reads `SKILL.md` and, before its first fit, builds the
helpers the pack's `tools.md` describes, one JSON result at a time:

- **`tools.md` is "the tools you build and their contracts".** It opens with
  the runtime every helper shares — paths (`runs/<pack>/<task>/<arm>/`,
  helpers under `runs/<pack>/helpers/`), `state.json` (fits used, frozen, test
  scored, memory on / off / frozen; written with `indent=1` so the freeze is
  the literal text `"frozen": true`), the append-only `traces.jsonl`, the data
  (`intent.md`'s `kind: csv | sklearn | synthetic`), the profile, the one
  four-way split (train 55 % / val 15 % / private 10 % / test 20 %, one seeded
  shuffle), the recipe as a scikit-learn pipeline, and the two-mirror rule —
  then one contract per tool: `load_splits`, `fit_recipe` (refuses the 25th
  call by reading `state.json`, a recipe outside the schema, a forbidden one),
  `score_test` (refuses before `FREEZE` and a second time), `save_model`,
  `scorecard` (the 14 fields), `write_loop_log`, `walk_path`, `read_memory`
  (with the policies), `write_card` (refuses a non-verifier caller, a card
  outside the schema, one whose text says `test` or `intent`, any write on the
  exam), `read_traces`, `lint_pack`, `propose` (one per visit, `patches:`, the
  20 % cap, the test rule untouchable), `apply` (refuses without the user's
  words in `proposals/<id>.approved`), `gate`, `private_score`, `rollback`,
  `read_pack`, `curve`, `exam`, and the method tools `rank_policies` (10),
  `write_plan` + `freeze_memory` (11), `contrast` (12), `skill_memory` (13),
  `archive` (14), `meter` (15), `map` (17). A pack's `## Forbidden` list names
  the tools it may not build or run; a test asserts they are absent from its
  procedure.
- **The agent writes the helpers** on first use, in any language (Python with
  scikit-learn is the natural choice; the recorded runs wrote one module or
  one script per tool), and reuses them. They are not shipped and not
  committed; the lesson pages quote what one recorded run produced.
- **State on disk.** `runs/<pack>/<task>/<arm>/state.json` and `traces.jsonl`;
  `runs/<pack>/versions/gen_NNN/` snapshots; `proposals/<id>.json` with
  `.approved` / `.rejected`; the pack is the other half of the state:
  `memory.json`, `config.md` with the off switches (front matter `memory: on |
  off | frozen`, `meta: on | off`), `roles/`, `operators.md`, `skill-memory/`.
- **Every rule a skill states that must hold absolutely is a refusal the
  contract makes the helper implement, and two of them are additionally
  enforced by a Claude Code hook**: every lesson ships `.claude/settings.json`
  with a PreToolUse hook as a shell one-liner (no script file) that blocks a
  Bash command containing `score_test` unless some `runs/**/state.json`
  contains `"frozen": true`, and a command containing `apply` unless a
  `proposals/*.approved` file exists — the playbook's "advisory skill +
  deterministic gate" split. It needs bash (Git Bash on Windows); agents
  without hooks get the helper-level refusal.
- **The human approval cycle** is the skill telling the agent: `propose`, show
  the diff, ask "approve / edit / reject", wait, write the user's exact words
  to `proposals/<id>.approved`, and only then `apply --approved "<the words>"`
  (`--edited` lands the user's version). The trace records who approved and
  with which words. Under `approval: gate` (lesson 09 on) the private split
  decides keep-or-rollback inside `gate`.
- **Curriculum across problems** (lessons 07, 09–16): the curriculum skill's
  procedure loops over `tasks/*/intent.md` in order — the agent orchestrates,
  its helpers measure (`curve` writes `curve.json`, `exam` the exam).
- **Where skills load from.** `rsi/step_NN/.claude/skills/<name>/` and the
  byte-identical `.agents/skills/<name>/`; a test asserts the two are equal,
  and the mirror rule makes every tool that changes a pack file write both.
- **Tests.** `test_step.py` per lesson (pytest, offline, seconds), the only
  Python shipped: the pack contract (front matter fields; every file the
  procedure names exists; every tool in `tools.md` Forbidden absent from the
  procedure; mirror identical; the hook line; `intent.md` fields and headings;
  no other `.py`) plus the lesson's own claims about its files; and, under
  `RSI_LIVE=1`, the recorded run: `claude -p` from the lesson directory with
  the README's prompt (`--allowedTools "Bash,Read,Write,Edit,Skill"
  --setting-sources project --strict-mcp-config`; approvals as `--continue`
  turns), then assertions on the artifacts the skill must leave (trace row
  count, `state.json` frozen and `test_scored == 1`, scorecard fields,
  `memory.json` changed or not per `config.md`, the approval words in the
  trace, `versions/` on a patch ...). Numbers vary between machines because
  the agent writes its own fit helper; acceptance is stated relatively
  (memory arm vs `MEMORY_OFF` arm at the same budget), which is what the
  paper's evidence standard asks for.

## Format — conforms to the Claude Academy *AI-native SDLC playbook*

The series is laid out like the course (six SDLC stages, one lesson per
step, ~1 hour of reading plus the runs). `rsi/README.md` is the course page:
title, one-line description, **What you'll learn** ("By the end of this
course, you'll be able to …"), **Who this course is for**, **Prerequisites**,
estimated time, and the lesson list grouped by stage. Every step README is a
lesson page with these headings, in this order, verbatim:

1. `# <Lesson title>` then one paragraph of concept (why this lesson exists).
2. `## Getting started` — prerequisites, what the previous lesson left on disk, what this one adds.
3. `## How to execute it` — numbered steps: the exact prompt to type into the agent, what the agent builds and runs, what you will be asked at each approval and what to answer, the headless `claude -p` line, how to reset.
4. `## What it looks like` — the pack files shown (front matter first; the contracts that carry the lesson), the transcript recorded with `claude -p` from the lesson directory (the helpers the agent wrote, the tool calls it made, their JSON results, the final answer), what to notice in it, and the `Files` tree.
5. `## Governance considerations` — who approves what, the hook, what the helper refuses (because the contract says so), what is and is not self-modified (autonomy attribution), the honesty of the numbers.
6. `## How to measure it` — the test claims of this lesson (each one line: claim → the test that proves it), the scorecard fields it reports, and how to run `python run_tests.py rsi`.
7. `## Next lesson` — one line; previous lesson linked too.

| SDLC stage | Lessons (steps) |
|---|---|
| Stage 1: Plan | 00 intent — capture what to improve, how, and what counts as success as `intent.md` + `acceptance.md` |
| Stage 2: Design | 01 regular harness · 02 loop engineering · 04 graph engineering with loops |
| Stage 3: Build | 03 meta generates the loop harness · 05 meta generates the graph harness · 06 the RSI harness · 08 meta generates the RSI harness |
| Stage 4: Test | 07 proof — locked test, transfer, the scorecard; `run_tests.py rsi` as the continuous eval |
| Stage 5: Deploy | 09 the RSI meta harness — approval cycles as gates (human, then the private gate), versions and rollback |
| Stage 6: Maintain | 10–14 RSI by method (Dream-RSI, RSIAgent, ModularRSI, Recuris, DGM, AIDE², MetaSkill-Evolve) — closing the loop on the metrics; 15 map |

Skills use the same layout the course teaches (`.claude/skills/<name>/SKILL.md`
with front matter naming when it triggers, then the instructions), and every
rule a skill states that must hold absolutely is a refusal the contract makes
the agent's helper implement, and for the two that matter most also the
lesson's hook — the course's "advisory skill + deterministic gate" split.

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
codelab's harness. The approval cycle is two contracts, `propose` and `apply`
(`propose → proposal id + diff`, the user's words → `proposals/<id>.approved`,
`apply --approved` lands), and every meta pack's `tools.md` states them.

### Part 1 — Harness engineering, no RSI (steps 01–05)

| Step | The pack (what is on disk) | The one idea | Rung |
|-----:|-----|------|------|
| 00 `intent` | `intent.md` (what to improve: Adult income > 50k; metric ROC-AUC; budget 24 fits per arm; allowed models; the locked test rule; the data source; the profile keys — YAML front matter + prose) and `acceptance.md` (the scorecard fields and the pass rule, written *before* any pack exists); the `intent` skill performs the `validate_intent` and `lint_pack` checklists of its `tools.md` by reading, and shows a widened pack refused | **Capture the intent first.** Humans specify what should be improved, how, and what counts as success — the framework paper's L1 precondition and the playbook's `intent.md`. Every later pack, writer and verifier reads this file; nothing may widen it. | L1 precondition |
| 01 `regular_harness` | `.claude/skills/adult-income-regular/`: `SKILL.md` (boot only this pack; fit the baseline; run the static 24-recipe list in order; pick best val; `score_test` once; `save_model`; stop; "next run boots this same text"), `tools.md` (allowed / forbidden), `schema.json` (task, target, metric, `n_fits: 24`, baseline, the 24 recipes) | A repeatable trainer. Same text every run, same waste every Monday. **The control arm, and not RSI.** The harness, the budget object, the locked test and the append-only trace arrive here. | B0 / AutoML |
| 02 `loop_harness` | `.claude/skills/adult-income-loop/`: `SKILL.md`, `loop.json` (`kind: counted_while`, `N: 24`, counter `t`, `error_still_counts`, `body`, `exit: FREEZE → score_test once → save_model`, `illegal: change N, reorder, second while, score_test before FREEZE, write memory.json`), `recipes.json`, `tools.md` + the `write_loop_log` contract (audit only) | **Loop engineering**: name the steps, the counter and the gate in a file; the tools enforce what the file declares. Still not RSI: the log is never read back; generation n+1 loads the same `loop.json`. | harness engineering |
| 03 `meta_generates_loop` | `.claude/skills/loop-writer/`: `SKILL.md` ("you do not fit models; given the intent write a loop pack: SKILL.md, tools.md, loop.json, recipes.json; then `propose` it and wait"), `tools.md` (`lint_pack`, `propose`, `apply` — never `fit_recipe`), `template/` (the loop pack with placeholders); the intent is `tasks/01_adult_income/intent.md` | **A meta harness whose output is a loop harness, under human approval.** The human sees the whole proposed pack, answers `y` / `n` / `edit`; `n` means nothing lands. One shot from a spec: generating twice yields the same proposal, and running the generated pack never changes it. Most "agent builds agent" demos stop here — not RSI yet. | L1: humans specify what / how / success; AI executes; human accepts |
| 04 `graph_harness` | `.claude/skills/adult-income-graph/`: `SKILL.md`, `graph.json` (nodes = legal operators; edges = hard dependencies; `score_test` a sink with `gate: freeze_only`; constraints: one encode / one scale / one model per path, no cycles), `paths.json` (baseline + 24 static paths with bindings), `loop.json` (the counted while now iterates over paths), `tools.md` + the `walk_path` contract; illegal path = skip and count, never invent | **Graph engineering with loops**: the job is a DAG, a recipe is a path, the loop walks paths. `graph.json` and `paths.json` are `mutable: false`. Still not RSI. | harness engineering |
| 05 `meta_generates_graph` | `.claude/skills/graph-writer/`: step 03's writer extended to emit `graph.json` + `paths.json` + `loop.json`; `lint_pack` now checks the DAG (no cycles, constraints, every path legal) and is proven on a planted `bad_paths.json` first; the proposal shows the graph as a node/edge list and the human approves, edits (e.g. removes an edge) or rejects | **A meta harness that generates a graph harness, under human approval.** `edit` is the interesting answer: the human's change is what lands, and the writer never sees the run results — still no feedback loop, still not RSI. | L1 |

### Part 2 — The first RSI, its proof, and the meta harnesses that make and improve it (steps 06–09)

| Step | The pack | The one idea | Rung |
|-----:|-----|------|------|
| 06 `rsi_harness` | `.claude/skills/adult-income/` (inner H): `SKILL.md` (boot order incl. `memory.json` unless `MEMORY_OFF` and `traces.jsonl`; for t in 1..24 read cards, propose ONE recipe from the schema, fit, append; FREEZE; `score_test` once; "only a meta pack may patch this pack"), `memory.json` (`[]`), `memory.schema.json` (`if` profile predicate → `then` prefer/forbid one field value, `evidence`, `counter`), `config.md` (the off switches), `tools.md` + `read_memory`; `.claude/skills/adult-income-verifier/` (input `{recipe, val_auc, error, profile}` only; IF/THEN cards with evidence and counterexample; refuse cards that mention test or intent; tools `read_traces`, `write_card`) | **The first RSI file.** A card is a constraint on the *next* proposal (the agent's `fit_recipe` refuses a forbidden recipe, as its contract says), and no one grades their own homework: the verifier pack boots with only the log. `memory: off` in `config.md` is the off switch: same 24 fits, the numbers must fall back; a second memory arm in the same lesson boots the first one's cards. | L4: deployment feedback revises persistent state under our acceptance rule |
| 07 `proof` | `eval.md` in the inner pack (24 vs 24 with `MEMORY_OFF`, the delete-file check, the scorecard fields, "test touched before freeze: no"); the `adult-income-curriculum` skill runs problems 1→6 in order (the agent orchestrates, its helpers measure), carrying the pack forward, and `curve` prints the **learning curve** (per problem: memory arm − `MEMORY_OFF` arm at the same budget, wasted fits, cards added/demoted); the same skill runs the frozen pack on problem 7 and `exam` reports | Locked test = you did not peek. The curve = experience from problem n helped on n+1: structural recursion you can see. The exam = effective recursion under a matched budget and an independent evaluation. The scorecard and the curve are the deliverables of every later step too. | evidence standard |
| 08 `meta_generates_rsi` | `.claude/skills/rsi-writer/`: step 05's writer extended to emit the inner pack **and** the verifier pack, `memory.schema.json` and `eval.md` from the intent; the lint refuses a verifier without its contract line (proven on a planted `bad_verifier.md`); the proposal shows the verifier contract first and the human must approve it (it is the acceptance rule) | **A meta harness that generates the RSI harness, under human approval.** The human is approving a *mechanism that will change itself later*, not a one-off pack — the README says so and shows the diff the human sees. | L1 for the generation; what it generates runs at L4 |
| 09 `rsi_meta_harness` | `.claude/skills/adult-income-meta/` (MH): reads traces + memory + inner pack; writes **one** proposal per visit — new cards, a small `schema.json` forbid, or the search-policy line; size cap 20 %; no `score_test`; `versions/` per generation; `private_score` on a split the inner pack never sees; the actor ships `Search policy: static` and the first patch flips it. Two modes on disk: `approval: human` (every generation's patch goes through the human cycle) and `approval: gate` (the private gate decides keep-or-rollback and the human only sees the log). the curriculum skill runs inner (problem n) → meta → inner (problem n+1) across the whole curriculum, one generation per problem; `META_OFF` | **The RSI meta harness that improves the harness — problem by problem.** Problem 1 teaches the pack encoding and class weights, problem 3 teaches it multiclass metrics, problem 5 demotes a superstition; by the exam the pack is the expert and the model is unchanged. Generation n+1 is RSI only if it boots what generation n wrote; the reboot is the recursion. Under `approval: human` the human is the acceptance rule (L4); under `approval: gate` the system revises its own improver's policy line behind a protected evaluator (L5 flavour). The archive rule and the gate itself stay human — say so. Rollback and version history are safe inheritance made concrete. | L4 → L5 flavour, switchable in one line |

### Part 3 — RSI by method, one published system per step, same curriculum (steps 10–16)

Each step is a variant of the step 06/09 packs plus at most one new tool, so
`diff -r` between two methods shows exactly what the method changes. Every
method step reports the step 07 scorecard (matched budget, one test score,
transfer), runs under the step 09 approval cycle, and says which file improved.

| Step | Method (paper) | The pack | What improves / the one idea |
|-----:|-----|------|------|
| 10 `rsi_dream` | Dream-RSI (arXiv:2609.14858) | `policies.md` (random, neighbours-of-top-3, prefer-untried-family, obey-memory); the `rank_policies` contract: replays `traces.jsonl` as a simulator, scores each policy best-of-first-k over the *logged* recipes with zero fits, unvisited picks = "unknown"; the meta pack proposes the winner as the inner **search-policy line**; the next online lap grows the log | **The search policy.** History is an exact gym for the recipes you visited and silent elsewhere; recursion pays only if the next lap visits new places (saturation shown, not hidden). |
| 11 `rsi_agent` | RSIAgent (arXiv:2609.15364) | three packs: `curriculum` (picks the next experiment by uncertainty `u = (1−success) + c/(n+1)`, broad phase large `c`, deep phase small `c` + fault rate), `actor` (proposes and runs), `verifier` (sees only the world result); memory frozen before `score_test` and reused on the transfer table | **The memory, chosen on purpose.** Broad-then-deep spends the same fits on higher-information experiments; frozen memory at test is what makes the comparison fair. |
| 12 `rsi_modular` | ModularRSI (arXiv:2609.14857) | the inner pack split into five files that mirror the paper's modules (`agent_loop.md`, `tool_use.md`, `observation.md`, `context.md`, `completion.md`); a disjoint pool of synthetic tables (`pool/NN/intent.md`, never the eval table); the `contrast` contract pairs a success and a failure on the same task and names the module; the meta pack proposes a patch to **one module**, validates on the pool, then integrates; transfer shown across two actor packs | **A harness module, evolved off the benchmark.** Contrast localises the bug to a module; the benchmark-disjoint pool kills leaderboard overfitting; a patch that helps both actors improved the workshop, not one model's quirks. |
| 13 `rsi_skill_memory` | Recuris (arXiv:2608.24876) | memory as a **skill package**: `skill-memory/manifest.yaml` + markdown skill cards (one per situation), a small `working.md` the actor rewrites per run ("what I am doing, which cards apply"); the meta agent turns execution evidence into localised, validated card updates; gains reported by horizon | **Experiential + working memory.** Skill selection is grounded in current need, not the whole history; the memory is git-native (files you can diff). |
| 14 `rsi_self_modifying` | Darwin Gödel Machine lineage (DGM, arXiv:2505.22954; Mendel / Huxley GM as reading) | the meta pack may propose rewrites of the inner pack's **`SKILL.md` and `loop.json` themselves** (the harness source), keeping an `archive/` of variants with their held-out scores and choosing parents from the archive, one generation deep, behind the private gate and the human cycle | **The agent's own source.** The empirical Gödel machine: keep an archive of stepping stones, expand promising ones; the archive rule and the gate stay human — say what is and is not self-modified. |

| 15 `rsi_aide2` | AIDE² (Weco AI, July 2026; tech report announced, code not released) | inner loop = the step 06 pack as an AIDE-style **tree search over solutions** with three operators (`draft`, `debug`, `improve`) and an eval reviewer that extracts the score from the run; outer loop = a meta pack that **rewrites the inner pack's operator text** and keeps the rewrite only if it beats the previous best **across the whole heterogeneous curriculum under a fixed cost budget** (fits and tokens, metered by the harness); three reward-hacking guards the outer loop must keep: an anti-overfitting line in every operator prompt, a hard guard that re-runs a suspicious score, a statistical layer that discards outlier successes | **Autoresearch on autoresearch.** Keep-if-better across many problems under one budget is what turns "a better run" into "a better researcher"; the guards are why the score means something. Reported: seven successive improved versions in 100 outer steps, 16× context compression — *reported, unverified* until the report and AIDE85 are released. |
| 16 `rsi_meta_skills` | MetaSkill-Evolve (arXiv:2607.05297) | two timescales on one frozen model: **task skills** (the inner pack's cards and policy line) evolve every problem; **meta-skills** (the meta pack's own five roles as files — `analyzer.md`, `retriever.md`, `allocator.md`, `proposer.md`, `evolver.md`) evolve every k problems by the same pipeline, with no extra model or objective; the human cycle approves meta-skill changes, the private gate approves task-skill changes | **The improver's skills improve too — slowly.** This is the "and so on": the pack that patches the pack is itself a pack with a version history, and its changes are rarer and gated harder. |

### Part 4 — Map (step 17)

| Step | Adds | The one idea |
|-----:|------|--------------|
| 17 `map` | README + the `rsi-map` skill (`ladder.md` + the `map` contract) that prints the ladder with steps 01–16 placed; the learning curve of every method on the same curriculum side by side; the file-by-file table (regular vs loop vs graph vs generated vs RSI vs each method, and who approved what); ScienceBuddy (arXiv:2609.17523, harness then weights, reading only) and OpenAI's stated priority as the rungs this series refuses to touch; the terminology table (self-refine, learning, self-organise/emergence, AutoML, bounded, genuine); the acceptance test; every external number marked *reported* with its source | You recognise the nouns because you built the toy — and you can point at which file each method changed and who approved it. |

Eighteen small steps. The contracts are the gates, the agent builds them,
the tests check the contracts offline and record the runs live; a lesson is
*run* by opening a coding agent in its directory, which asks you at every
approval.

## What each test proves (offline: the pack contract and the lesson's claims about its files; live under `RSI_LIVE=1`: the recorded run)

Offline, every lesson: front matter (`name`, `description`, `metadata.type / version / rsi`), the four headings; every file the procedure names exists; every tool in `tools.md` Forbidden is absent from the procedure; `.claude/skills` == `.agents/skills`; the hook line gates `score_test` on `"frozen": true` and `apply` on `.approved`; every `intent.md` has the front matter fields and the five body headings; no `.py` but `test_step.py`. Then:

- 00: `intent.md` is the first curriculum problem byte for byte; the acceptance fields are exactly the 14 scorecard fields; the widened pack breaks three rules of the checklist; the seven problems are in order; the skill has no write step. Live: nothing changed; the report names 24, FREEZE, 48, the 14 fields and the seven problems.
- 01: the schema is the intent plus 24 distinct static recipes; the procedure is static and scores once; the contracts state the refusals. Live: 24 fit rows 1..24, frozen, `test_scored` 1, FREEZE before `score_test`, the 14-field scorecard, `model.pkl`.
- 02: `loop.json` declares the counted while; the log is never read back. Live: `t` reached `N`, 24 log lines, one `score_test` after FREEZE, the pack byte-identical.
- 03: the template fills into lesson 02's pack and lints; the writer waits. Live: a proposal and no landed pack after turn one; after `approve` the five files equal the fill in both mirrors, the trace `propose` then `apply` with the word.
- 04: a DAG with `score_test` behind the gate; 24 paths, one planted illegal, 23 recipes; skipped and counted. Live: the illegal row at `t` 17, ≥ 22 scored fits, the three files unchanged.
- 05: the fill is a legal graph pack (lesson 04's `graph.json`); the bad paths are refused; lint before propose before apply. Live: the refusal shown, then `edit: remove path p24` lands 23 paths.
- 06: the memory ships empty; the schema types a card; `config.md` has both switches; the verifier is blind by contract; the actor never writes a card; the pairwise rule and its thresholds. Live: three arms scored once; empty memory = control; typed clean merged cards; `memory-r2` booted them; the verifier's event.
- 07: `eval.md` states the claims; six problems then the exam without a verifier; the exam intent forbids writing; `curve` / `exam` never invent. Live: 12 curriculum arms + 10 exam arms, six curve rows, `pack_unchanged`, `no_card_written`.
- 08: the fill is lesson 07's two packs; the contract line is mandatory; the human approves the contract first. Live: the contract shown verbatim, then `approve` lands ten files.
- 09: the actor ships `static`; the two meta packs share the rule and differ in who decides; one change per visit under the cap; the curriculum re-reads the actor; the gate uses the private split. Live: the gate curriculum (versions, gate events, curve, exam) and the human visit (no version until `approve`).
- 10: five policies; `rank_policies` spends nothing and counts unknowns; only the policy line, behind the gate. Live: rank events with `fits_spent` 0.
- 11: the uncertainty rule with its `c` values; the actor runs the plan and freezes memory before the test. Live: broad touches every family first, `broad` then `deep`, `freeze_memory` before `score_test`.
- 12: two actors differ in `context.md` only; the pool is disjoint; one module on the pool. Live: both actors on both pool tables, no curriculum table touched, a contrast, a gate.
- 13: the skill package; selection by need; one validated update per visit. Live: `working.md` rewritten, horizons, one version per update.
- 14: only `SKILL.md` and `loop.json` are self-modified; the archive and parent rule; the gate before the human. Live: the archive with a score, a gate event, `approve` landing the rewrite.
- 15: every operator carries the guard; keep-if-better across the set under one meter, no token count. Live: `v1` and `v2` with equal fits, a meter decision, four guards.
- 16: five roles carry the numbers; two timescales, two gates; a version history for the meta pack. Live: slow-loop events only on problems 3 and 6, landed only on `approve`.
- 17: the ladder places every lesson; the map never invents. Live: nothing changed, every recorded lesson named.
- All: `python run_tests.py rsi` and `python check_snippets.py rsi` green.

## Validation of the source tutorial against the papers (18 Sep 2026)

Repos and abstracts checked: RSIAgent (arXiv:2609.15364, AetherLabsAI/RSIAgent), Dream-RSI (2609.14858, code "being prepared"), ModularRSI (2609.14857; modules are Agent Loop, Tool Use, Observation Management, Context Management, Task Completion Detection — not "verification"), ScienceBuddy (2609.17523, inner harness loop + outer RL loop), Recuris (2608.24876, +32.2 on the longest tasks), the framework paper (2609.11873) and the July corpus survey (2607.07663). The tutorial's descriptions match; its specific numbers (162×, 71.97→78.98, 47.57→52.43, 8×A100, gpt-6-astra as improver) are not in the abstracts and stay *reported*. Conceptual corrections the series makes: "bounded vs strong" is too coarse (use the rungs + structural/effective); the locked test split is the wrong hero test (transfer table); free-text cards are not executable (typed cards + tool enforcement); a verifier that sees only `{recipe, val_auc, error}` cannot write the cards shown (it also gets the profile); single-seed "delete the file" claims are noise (paired seeds, matched budget); "replay each policy on the log" is under-specified (rank logged recipes, unvisited = unknown); no rollback anywhere (versions + private gate).

## Repo wiring

`rsi/README.md` (series codelab, top-down); `run_tests.py` / `check_snippets.py` already know `rsi/step_*`; `rsi/data/` bundled sample + licence note (no script); `rsi/tasks/NN_<name>/intent.md` the curriculum; no `rsi/tools/`, no `rsi/hooks/`; `scikit-learn`, `pandas`, `numpy`, `pyyaml` in `requirements.txt` for the agent's helpers and the tests.
