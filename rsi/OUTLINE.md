# Zero to Hero: Recursive Self-Improvement (RSI) — outline

**The searcher gets smarter. The model weights do not. You can measure both.**

This series does for RSI what the root codelab does for the harness: one idea
per step, every step a directory you can run, every step a test that runs
without a key or the network, and a README that shows the code with the
reason under each snippet. The same three rules hold: every fit goes through
one place, the transcript of trials (the log) is append-only and cheap to
replay, and errors are results.

## The job (real software, no toy factory)

Raise the ROC-AUC of a tabular classifier on **Adult Census Income** under a
hard budget of **24 `fit()` calls per arm**, without touching the locked test
split, without changing any LLM weights. Then prove the *searcher* improved,
not just the model: freeze the memory, run the same budget on a **second
table** it never saw, and compare against the arm that had no memory.

Data: a bundled 6k-row sample of Adult (UCI, public domain) so every step and
every test runs offline in seconds; the loader fetches the full 48k rows from
OpenML into a cache when the network is there. A second bundled table (Bank
Marketing sample, or a synthetic shifted table when offline) is the transfer
task. Models: `LogisticRegression`, `RandomForest`, `HistGradientBoosting`
(sklearn, CPU). Metric: ROC-AUC on the validation split during search; the
test split is scored **once**, after freeze, by a gate object that raises on a
second call.

## Definition used throughout (and the terms it is not)

*Bounded RSI*: a persistent mechanism (a file) that later runs load, that
was written by earlier runs, behind a verifier the writer cannot game, with an
off switch. Delete the file: quality must fall. The series distinguishes it in
code and in tests from *self-refine* (better answer this turn), *learning*
(any update), *self-organisation / emergence* (no file the next generation
boots), *AutoML* (search with no durable theory of why), and *strong RSI*
(training the next model — reading only).

## Parts and steps

Every step: `rsi/step_NN_<name>/` with the code, `test_step.py` (offline,
deterministic, seeds fixed, small synthetic table for speed), `README.md`
(what it adds, why, code walk-through, run it + expected output, what breaks
without it, gotchas, what the next step adds).

### Part 1 — The job, the budget, the control arm (steps 00–03)

| Step | Adds | The one idea |
|-----:|------|--------------|
| 00 `setup` | data loader (bundled sample + OpenML cache), locked splits, `Budget(24)`, `LockedTest` | The two off switches are objects, not promises: the budget raises on the 25th fit, the test gate raises on the second score. |
| 01 `baseline` | fixed recipe pipeline (`ColumnTransformer` + `LogisticRegression`), ROC-AUC, the scorecard file | A number nobody can argue with. Every later step reports against it. |
| 02 `trial_log` | recipe schema (`scale`, `encode`, `model`, one hparam, `class_weight`), `fit_recipe(recipe) -> {val_auc, error, seconds}`, append-only `traces.jsonl` | A trial is one dict and one fit; the log is the world every later step replays. |
| 03 `random_search` | the control arm: 24 random recipes, val curve, best-val recipe, paired seeds ×5, mean ± std | Without a control arm you cannot claim RSI. With one seed you cannot claim anything. |

### Part 2 — The four knobs, one at a time (steps 04–09)

| Step | Adds | The one idea |
|-----:|------|--------------|
| 04 `memory_cards` | `memory.json`, executable cards (`condition` on the dataset profile → `prefer` / `forbid` a recipe field value, `evidence`, `counter`), `apply_cards(space, cards)`, a rule-based verifier that only sees `{recipe, val_auc, error, profile}` | Memory is a constraint on the next proposal, not a diary. Same 24 fits; quality must rise or waste must fall; delete the file and it must fall back. |
| 05 `verifier_contract` | the verifier as a type that cannot receive actor intent, paired-comparison evidence (recipes that differ in one field), merge/decay, a size cap, the superstition test | No one grades their own homework. A wrong card must be demotable by counterexamples, or memory RSI becomes permanent folklore. |
| 06 `freeze_and_gate` | `FREEZE`, best-val selection, the single `score_test`, the acceptance scorecard (baseline test AUC, RSI test AUC, fits per arm, cards readable, delete-file check, test touched before freeze: no) | The proof is a number you earned once, not a curve you tuned. |
| 07 `curriculum` | broad-then-deep over recipe families: `u = (1 − success) + c/(n+1)`, large `c` first, then shrink `c` and add the fault rate | Same dollars, higher-information experiments. Curriculum makes the trials smarter, not the intern. |
| 08 `dream_replay` | policies as small Python functions that *rank the logged recipes*, scored on `traces.jsonl` with zero fits (best-of-first-k), a leaderboard, deploy the winner for the last 8 fits, the saturation demo | History is an exact gym for the recipes you visited and silent elsewhere. Recursion only pays if the next online lap visits new places. |
| 09 `transfer` | the second table, frozen memory, same 24-fit budget, memory arm vs random arm, per-card transfer report (which cards helped, which were Adult superstitions) | The locked test proves you did not peek. The second table proves the *searcher* got smarter. The tutorial conflates the two; this step separates them. |

### Part 3 — The harness is files (steps 10–13)

| Step | Adds | The one idea |
|-----:|------|--------------|
| 10 `harness_as_skill` | the inner pack `skills/adult-income/` (`SKILL.md`, `tools.md`, `schema.json`, `memory.schema.json`, `eval.md`), a boot loader that reads only those files, `MEMORY_OFF` / `META_OFF` | You configure a harness by writing a file the next process boots, never by talking. Regular harness first: same text every run, no RSI. |
| 11 `meta_harness` | the outer pack `skills/adult-income-meta/`: reads traces + memory + inner files, writes **one** patch per visit (cards, a `schema.json` forbid, or one search-policy line), size cap 20 %, never scores test | Generation n+1 is RSI only if it boots what generation n wrote. The reboot is the recursion. |
| 12 `private_gate` | a second validation split the inner loop never sees; a meta patch is kept only if that private score does not drop (OpenRSI's move); the Goodhart demo (a patch that wins val and loses private) | The improver must not grade its own homework either. Prompt-length inflation and benchmark hacking appear the moment you remove this. |
| 13 `modular_harness` | the searcher split into `propose / observe / context / verify / loop` modules; contrastive win/fail pairs on a disjoint pool of synthetic tables; patch one module, validate on the pool, then integrate; transfer across actors | ModularRSI shrunk: evolve off the benchmark, localise the bug to a module, gate the patch. |

### Part 4 — The model enters, and the real systems (steps 14–17)

| Step | Adds | The one idea |
|-----:|------|--------------|
| 14 `llm_actor` | the proposal is one model call that reads the cards (OpenAI-compatible, same env vars as the root codelab); verifier stays code; fake model in tests; the equal-budget comparison against the random actor | Asymmetric RSI: a bigger model writes the notebook of a smaller loop. Useful, honest, not a closed loop of equals. |
| 15 `llm_verifier` | the verifier as a model call under a strict JSON schema (cards only), rejection of cards that mention test or intent (schema + regex), evidence still counted by code | The contract survives the move to a model because the contract is enforced by code around the call. |
| 16 `inside_the_harness` | the two packs run as skills of this repo's coding harness (step 45's `harness/`): hooks as gates (PreToolUse blocks `score_test` before `FREEZE`), the eval runner (step 30 shape) runs the 24-vs-24 comparison, replay/trace for the run | The RSI loop is just another thing the harness hosts: skills, hooks, evals and the trace log are all already there. |
| 17 `map_and_honesty` | the comparison README (step 51 shape): what we built vs RSIAgent / Recuris / Dream-RSI / ModularRSI / ScienceBuddy / DGM / OpenRSI; which knob each turns; what needs Docker/KVM/8×A100; the terminology table; the acceptance test; every external claim marked verified or unverified | Reading only. You recognise the nouns because you built the toy. |

Optional appendix (reading, no code): the ScienceBuddy double loop (harness
then GRPO), the Gödel-machine lineage (DGM, MGM, HGM), OpenAI's stated
priority — with the honest line that none of it is in these steps.

## What each step must prove in its test (offline, no key)

- 00: the 25th fit raises; the second `score_test` raises; splits are disjoint and stable across runs.
- 03: paired seeds — the control arm's mean is reproducible bit-for-bit.
- 04: same budget, memory arm ≥ control on mean val AUC across 5 seeds; deleting `memory.json` restores the control numbers.
- 05: a planted wrong card is demoted after k counterexamples; a card that mentions `test` or intent is rejected; the verifier type has no field for the actor's reasoning.
- 06: test scored exactly once; scorecard fields all present.
- 07: fewer wasted fits on solved families than uniform sampling (counted, not eyeballed).
- 08: dreaming makes zero `fit` calls (counted); a policy that prefers unvisited recipes scores "unknown", not high.
- 09: frozen memory on the second table beats the random arm on ≥ 3 of 5 seeds, and the report names the cards that did not transfer.
- 10/11: `MEMORY_OFF=true` reproduces step 03; generation n+1 boots the files generation n wrote (checksum in the trace).
- 12: a patch that raises val and lowers private is rejected.
- 13: a module patch validated on the disjoint pool transfers to the held-out actor.
- 14/15: with a fake model the loop makes exactly 24 fits; a hallucinated recipe field becomes an `Error:` result, never a crash.
- 16: `run_tests.py rsi` and `check_snippets.py rsi` cover the series; the hook blocks `score_test` before freeze.

## Errors and gaps in the source tutorial that the series corrects

1. **Locked test ≠ proof of RSI.** The tutorial's "hero test" is the test split of the same dataset. That proves you did not peek; it does not prove the searcher improved. The proof is a second task with frozen memory (step 09).
2. **Free-text IF-THEN cards are not executable.** "IF high cardinality THEN do not use ordinal encode" cannot bias a sampler. Cards are typed constraints on the recipe space with a dataset-profile condition (step 04).
3. **The verifier "sees only {recipe, val_auc, error}"** cannot write a card about cardinality or imbalance. It also gets the dataset profile — a fact about the environment, not the actor's story (step 05).
4. **One seed proves nothing.** Every comparison is paired across seeds with mean ± std; the pass rule is stated per seed (step 03 onward).
5. **Dream replay is under-specified.** "Replay each policy on the log" cannot score a policy that would pick recipes never fitted. Policies rank the logged recipes; unvisited picks score "unknown"; the saturation is shown, not hidden (step 08).
6. **Baseline test AUC "at the start"** is fine only if the number is written to the scorecard and never read by the search; the gate object enforces it (step 00/06).
7. **Some example cards are slogans**, e.g. ordinal encoding is often fine for tree models. Cards come from paired evidence in the log, never from the tutorial's prose (step 05).
8. **Paper numbers and ids** (162×, 47.57→52.43, arXiv ids dated 2609.*) are quoted from the source without verification. The repos exist (checked: RSIAgent, ModularRSI, ScienceBuddy; Dream-RSI code still "being prepared"); the numbers stay marked *reported, unverified* in step 17.
9. **"Delete the file, quality falls"** needs the same seeds and the same budget on both arms, or it measures noise (step 04's test).
10. **Curriculum over materials A/B/C** has no analogue in a single-dataset job; the series defines the arms as recipe families (step 07) and datasets in the transfer step (step 09).

## Repo wiring

- `rsi/README.md`: the series codelab (same shape as `genui/README.md`), top-down.
- `run_tests.py` and `check_snippets.py` learn the `rsi/step_*` layout (`python run_tests.py rsi`).
- `rsi/data/`: the bundled samples with their licence notes; `rsi/common/` shared code (loader, budget, gate, log) imported by every step so each step's directory holds only its idea.
- Dependencies: `scikit-learn`, `pandas`, `numpy` (added to `requirements.txt`); the model steps reuse the root codelab's `BASE_URL` / `API_KEY` / `MODEL`.
