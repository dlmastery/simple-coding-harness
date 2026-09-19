# Zero to Hero: Recursive Self-Improvement — a hello world (outline, v2)

**The searcher gets smarter. The model weights do not. You can measure both, turn it off, and roll it back.**

Hello world, not a research system. Concept first: every step adds exactly one
idea, the code stays small (a hundred-odd lines), every step runs offline in
seconds, and every step has a test that proves its one claim. Same shape as the
root codelab: a directory you can run, a README that shows the code with the
reason under each snippet, a test without a key.

## The job (real software, no toy factory)

Improve a tabular classifier on **Adult Census Income** under a hard budget of
**24 `fit()` calls per arm**. Then prove the *searcher* improved, not just the
model: freeze the memory and run the same budget on a **shifted synthetic
table** it never saw. A bundled 6k-row sample of Adult (UCI, public domain)
keeps everything offline; the loader fills the cache from OpenML when there is
a network. Models: `LogisticRegression`, `RandomForest`,
`HistGradientBoosting` (sklearn, CPU). Metric: ROC-AUC on the validation split
during search; the test split is scored **once**, after freeze, by a gate
object that raises on a second call.

## The definition we use (from the survey, not from a slogan)

The survey published last week — *The Last AI Built by Humans: Toward Genuine
Recursive Self-Improvement* (arXiv:2609.11873, 10 Sep 2026, revised 15 Sep) —
defines RSI as an autonomous, closed-loop process in which a system turns
experience into **persistent changes to itself across interaction rounds**
(parameters, harness, or improvement policy) such that those changes **affect
how later improvements are generated, evaluated, selected or consolidated**.
It draws three lines the hello world is built to respect:

- **B0, in-task improvement, is not RSI**: a better answer this turn with no
  persistent state change. AutoML and continual learning are not RSI either
  when the search space, objective, budget and acceptance test stay fixed by
  the designer.
- **Structural vs effective recursion**: a mechanism that is revised and
  reused (structural) is only worth something if the successor is stronger
  *under a comparable budget and an independent evaluation* (effective).
- **Three problems every claim must answer**: safe inheritance (rollback,
  version history, transfer tests), autonomy attribution (which decisions the
  AI took vs which were fixed procedure), reliable verification (protected
  evaluation, matched budgets — an improver that can query the grader learns
  to game it).

Its five autonomy levels are the ladder the steps climb: L1 execute and retain
validated improvements; L2 choose the improvement strategy; L3 choose what
experience to acquire; L4 revise persistent state from deployment feedback
under an external acceptance rule; L5 revise the improver/verifier/policy
itself. Every step says which rung it stands on and which parts stay human.

## Steps

Every step: `rsi/step_NN_<name>/` with the code, `test_step.py` (offline,
deterministic, seeds fixed, a small synthetic table for speed), `README.md`
(what it adds, why, code walk-through, run it + expected output, what breaks
without it, what it is not, what the next step adds). Shared code the steps
import lives in `rsi/common/` (loader, splits, budget, gate, trace log) so each
step directory holds only its idea.

| Step | Adds | The one idea | Rung |
|-----:|------|--------------|------|
| 00 `contract` | data loader (bundled sample + OpenML cache), locked splits, `Budget(24)` that raises on the 25th fit, `LockedTest` that raises on the second score, an append-only `traces.jsonl` | The off switch and the anti-peek gate are objects that raise, not promises in prose. The log is the world every later step replays. | — |
| 01 `control_arm` | the fixed baseline recipe; a recipe = one dict (`scale`, `encode`, `model`, one hparam, `class_weight`); `fit_recipe(recipe) -> {val_auc, error}`; random search, 24 fits, paired seeds ×5, mean ± std | Without a control arm you cannot claim RSI; with one seed you cannot claim anything. This is every paper's "without RSI" bar. | B0 / AutoML (deliberately not RSI) |
| 02 `memory` | `memory.json` of executable cards (`condition` on the dataset profile → `prefer` / `forbid` one recipe field value, `evidence`, `counter`); a rule-based verifier that receives only `{recipe, val_auc, error, profile}` — the type has no field for the actor's reasoning; paired-comparison evidence; a wrong card gets demoted by counterexamples | The card is a constraint on the *next* proposal, not a diary. No one grades their own homework. Delete the file: quality must fall on the same seeds and budget. | L4: deployment feedback revises persistent state; the acceptance rule (the verifier) is still ours |
| 03 `proof` | `FREEZE`; best-val selection; the single `score_test`; the acceptance scorecard; then the transfer run: frozen memory, same 24-fit budget, on the shifted synthetic table, memory arm vs random arm, per-card report (which cards helped, which were Adult superstitions) | The locked test proves you did not peek. The new table proves the *searcher* got better — that is effective recursion. The scorecard is the deliverable. | evidence standard: matched budget, protected evaluation, transfer |
| 04 `policy` | policies as small Python functions that *rank the logged recipes* (random, neighbours-of-top-3, broad-then-deep by family uncertainty `u = (1 − success) + c/(n+1)`, obey-memory); scored on `traces.jsonl` with zero fits (best-of-first-k); leaderboard; the winner gets the last 8 real fits | History is an exact gym for the recipes you visited and silent elsewhere (Dream-RSI's idea, honestly bounded). Curriculum spends the same fits on higher-information experiments (RSIAgent's broad-then-deep). | L2 strategy autonomy + L3 experience autonomy |
| 05 `harness_files` | the inner pack `skills/adult-income/` (`SKILL.md`, `tools.md`, `schema.json`, `memory.schema.json`); a boot loader that reads only those files; `MEMORY_OFF` / `META_OFF`; the meta pack `skills/adult-income-meta/` that reads traces + memory + inner files and writes **one** patch per generation (cards, a `schema.json` forbid, or one search-policy line), size cap 20 %, never scores test; a private validation split the inner loop never sees; a patch is kept only if the private score does not drop, else **rolled back** (git-style version history of the pack) | Generation n+1 is RSI only if it boots what generation n wrote; the reboot is the recursion. The private gate and the rollback are the survey's "reliable verification" and "safe inheritance" made concrete. | L5 flavour: the search policy line of the improver is revised; archive/acceptance rule stay human (say so: autonomy attribution) |
| 06 `map` | reading only: the ladder with each step placed on it; what the five real systems change (RSIAgent/Recuris memory; Dream-RSI search policy; ModularRSI harness modules; ScienceBuddy harness then weights; DGM the agent's own source); the terminology table (self-refine, learning, self-organise/emergence, AutoML, bounded, genuine); the acceptance test; every external claim marked verified or reported | You recognise the nouns because you built the toy. | — |
| 07 `llm_actor` (optional, needs a key) | the proposal is one model call that reads the cards; verifier, budget, gate, memory unchanged; a fake model in the test; the same 24-vs-24 comparison | Asymmetric RSI: a bigger model writes the notebook of a smaller loop. The contract survives the move to a model because code enforces it around the call. | same rungs, different actor |

Seven small steps (six core). Dropped from v1 on purpose: the modular-harness
toy (ModularRSI) and running inside the coding harness — both are mentioned in
step 06 and nothing else depends on them.

## What each test proves (offline, no key)

- 00: the 25th fit raises; the second `score_test` raises; the splits are disjoint and byte-stable across runs; the log is append-only.
- 01: the control arm's numbers are reproducible per seed; the baseline is written to the scorecard and never read by the search.
- 02: same budget and seeds, the memory arm's mean val AUC ≥ control on 5 seeds and its wasted fits are fewer; deleting `memory.json` restores the control numbers exactly; a planted wrong card is demoted after k counterexamples; a card that mentions `test` or intent is rejected; the verifier type cannot receive the actor's reasoning.
- 03: test is scored exactly once; all scorecard fields present; on the shifted table the frozen memory beats the random arm on ≥ 3 of 5 seeds and the report names at least one card that did not transfer.
- 04: dreaming makes zero `fit` calls (counted by the budget object); a policy that prefers unvisited recipes scores "unknown", never a number; broad-then-deep wastes fewer fits on a solved family than uniform sampling (counted).
- 05: `MEMORY_OFF=true` reproduces step 01 bit-for-bit; generation n+1 boots the files generation n wrote (checksum recorded in the trace); a meta patch that raises val but lowers the private score is rejected and the pack is rolled back to the previous version.
- 07: with a fake model the loop makes exactly 24 fits; a hallucinated recipe field becomes an `Error:` result, never a crash.

## Validation of the source tutorial against the papers (done, 18 Sep 2026)

Checked on arXiv / GitHub. The tutorial's *descriptions* of the five systems
match their abstracts; several of its *specifics* do not, and its conceptual
frame is coarser than the survey's.

| Claim in the tutorial | Status |
|---|---|
| RSIAgent (arXiv:2609.15364): curriculum/actor/verifier, broad-then-deep, memory frozen at test time, Kimi-K3 + GLM-5.3 beating GPT-6 on OSWorld-v2 and Agents' Last Exam; repo AetherLabsAI/RSIAgent, Apache-2.0, Python 3.12 + Docker/KVM | **Verified** (abstract and README). The exact numbers 71.97→78.98 / 83.75→84.82 are not in the abstract: *reported, unverified*. |
| Dream-RSI (arXiv:2609.14858): discovery history as a replay simulator, offline policy refinement, redeploy, pool grows; repo zhengkid/Dream-RSI | **Verified** as described; the repo lists full code and reproduction scripts as "being prepared". "162× fewer agent calls", "1.7–2.4× fewer generations" are not in the abstract: *reported, unverified*. |
| ModularRSI (arXiv:2609.14857): five modules, contrastive success/fail on the same task, benchmark-disjoint 2,000-task pool, transfer across models; repo IQuestLab/ModularRSI, CC BY-NC 4.0 + Apache-2.0 | **Verified**; the module list in the paper is *Agent Loop, Tool Use, Observation Management, Context Management, Task Completion Detection* — the tutorial's fifth module "verification" is the README's naming, not the paper's. TB2.0 47.57→52.43 is in the README, not the abstract. |
| ScienceBuddy (arXiv:2609.17523): inner harness loop with frozen model, outer RL loop under the improved harness; repo Gen-Verse/ScienceBuddy with algorithm.md / experiments.md | **Verified**. Qwen3.5-4B, SkyRL/GRPO, 8×A100 and "gpt-6-astra as improver" are repo/tutorial details, not abstract claims: *reported*. |
| Recuris (arXiv:2608.24876): evolve Skill Memory, agent frozen, gains grow with horizon, +32.2 on longest tasks | **Verified** (abstract: 35 of 37 model-benchmark pairs, +32.2 on the longest tasks). The tutorial's memory formula `M=(E,W,ρ,C)` is not in the abstract. |
| "Survey arXiv:2609.11873 with an L1–L5 autonomy taxonomy" | **Verified**; it is a framework/roadmap paper (37 authors) with five autonomy levels and the Headroom-Closed Index. |
| "1,250-paper corpus arXiv:2607.07663" | **Verified** (July 2026 survey, two axes: what improves × loop closure). |
| "Bounded vs strong RSI" as the only distinction | **Too coarse.** The survey has five rungs plus B0, and separates structural from effective recursion; the hello world uses those. |
| The locked test split is the "hero test" | **Wrong target.** It proves no peeking; the survey's "effective recursion" needs a stronger successor on an independent evaluation — the transfer table (step 03). |
| Free-text IF-THEN cards | **Not executable**; cards are typed constraints (step 02). |
| Verifier sees only `{recipe, val_auc, error}` | **Cannot write the cards the tutorial shows** (cardinality, imbalance); it also gets the dataset profile (step 02). |
| One seed, "delete the file and quality falls" | **Noise.** Paired seeds, same budget, mean ± std (steps 01–03). |
| "Replay each policy on the log" | **Under-specified**; policies rank logged recipes, unvisited picks are "unknown" (step 04). |
| No rollback anywhere | **Missing** what the survey calls safe inheritance; step 05 versions the pack and rolls back on regression. |
| OpenAI "top priority" essay, Pachocki | Not checked; stays *reported* and out of scope. |

Sources: arXiv 2609.11873, 2609.15364, 2609.14858, 2609.14857, 2609.17523,
2608.24876, 2607.07663; GitHub AetherLabsAI/RSIAgent, IQuestLab/ModularRSI,
zhengkid/Dream-RSI, Gen-Verse/ScienceBuddy.

## Repo wiring

- `rsi/README.md`: the series codelab, top-down.
- `run_tests.py` / `check_snippets.py` learn the `rsi/step_*` layout (`python run_tests.py rsi`).
- `rsi/data/`: the bundled Adult sample with its licence note; `rsi/common/`: loader, splits, budget, gate, log.
- Dependencies: `scikit-learn`, `pandas`, `numpy` added to `requirements.txt`; step 07 reuses `BASE_URL` / `API_KEY` / `MODEL`.
