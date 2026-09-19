# Lesson 17 - The map: the ladder, every method's curve side by side, and who approved what

You built the toy, so the nouns now point at files. This lesson is the map
back to the literature: the framework paper's ladder (arXiv:2609.11873v2)
with lessons 01-16 placed on it by the decision each one moved from the
designer to the system; every method's learning curve on the same
curriculum, side by side, read from the `curve.json` each lesson's `run.py`
wrote; the file-by-file table of what improved and who approved it; the
rungs this series refuses to touch; the six words people use for all of
this; and the acceptance test. Every number quoted from elsewhere is marked
*reported* with its source, and none of them was measured here.

## Getting started

Lesson 16 left the two clocks. This lesson adds `run.py`, which reads the
runs the other lessons left under their `runs/` directories and prints the
map; nothing is fitted. Run the lessons first (each `FAKE_MODEL=1 python
run.py` takes under a minute on this machine) or read the table below.

## How to execute it

1. Print the map:

   ```bash
   cd rsi/step_17_map
   python run.py
   ```

   ```powershell
   cd rsi\step_17_map
   python run.py
   ```

   No model, no key, no approval: it reads files.
2. Tests: `python run_tests.py rsi`.

## What it looks like

`run.py` holds the map as data:

```python
LADDER = [
    ("not RSI (B0 / AutoML / harness engineering)", ["01", "02", "04"], "none: a fixed procedure", "everything"),
```

```python
CURVES = {
    "07 proof": "step_07_proof/runs/curriculum/curve.json",
```

Expected output, on this machine, after every lesson's `run.py` had been
run once with `FAKE_MODEL=1` (the ladder, the file table, the terms and the
reported numbers are elided here; they are the tables below):

```text
Learning curves on the same curriculum (memory arm - MEMORY_OFF arm, best val, per problem):
  lesson               adult_income  breast_cancer           wine         digits  synth_shift_a  synth_shift_b  wasted m/c
  07 proof                  +0.0000        +0.0012        +0.0000        +0.0000        +0.0024        +0.0646       19/33
  09 meta (human)           +0.0000        +0.0012        +0.0000        +0.0000        +0.0024        +0.0646       19/33
  09 meta (gate)            +0.0000        +0.0012        +0.0000        +0.0000        +0.0024        +0.0646       19/33
  10 Dream-RSI              +0.0000        +0.0012        +0.0000        +0.0001        +0.0000        +0.0646       29/33
  11 RSIAgent               +0.0000        +0.0000        +0.0000        +0.0000        +0.0000        -0.0270       27/33
  13 Recuris                +0.0000        +0.0000        +0.0000        +0.0000        +0.0024        +0.0646        6/33
  14 DGM                    +0.0000        +0.0012        +0.0000        +0.0000        +0.0000        +0.0000       33/33
  16 MetaSkill              +0.0000        +0.0012        +0.0000        +0.0000        +0.0024        +0.0646       19/33
```

How to read it. Wine and digits are saturated for this recipe space
(every recipe scores 1.0 or 0.999), so nothing learns there and the
honest gap is zero. The cards-and-policy-line family (07, 09, 16) reaches
the same +0.065 on problem 6 and wastes 19 fits over the curriculum
against the static walk's 33; Recuris (13) gets the same gain from its
skill package with the fewest wasted fits (6) because the card it shipped
already applied on Adult. Dream-RSI (10) flips the line to `random` on the
easy problems and pays for it on problem 5. RSIAgent (11) spends its deep
phase where the faults are and loses 0.027 on problem 6 - a curriculum
that buys information, not validation points. The DGM lineage (14) never
left `static`: every rewrite scored below it on the held-out benchmark
and the archive says so. AIDE² (15) and ModularRSI (12) do not run the
curriculum arm-against-arm and are not in this table; their numbers are on
their own pages (a rewrite rejected at -0.0001 on the set; one module
patched, 0.7925 -> 0.8571 on the eval table).

### The ladder

| Rung (arXiv:2609.11873v2) | Lessons | The decision the system takes | What stays human |
|---|---|---|---|
| not RSI: B0 self-refinement, AutoML, harness engineering | 01, 02, 04 | none - a fixed procedure | everything |
| L1: humans specify what to improve, how, and success; AI executes a generation procedure | 00, 03, 05, 08 | renders a pack from `task.json` | the spec, the acceptance (`y` / `n` / `edit`), the verifier contract |
| L2: how to improve - the search strategy | 10, 12 | ranks policies on the log; names the module to patch | the policy library, the module boundaries, the pool |
| L3: which experience to acquire | 11 | picks the next experiments by uncertainty | the uncertainty rule, the phase lengths |
| L4: revise persistent state from deployment feedback under an acceptance rule | 06, 07, 09 (human), 13 | writes and demotes cards; one patch per generation | the verifier contract, the off switches, the human at the prompt |
| L5 flavour: revise the improver / verifier / successor procedure itself | 09 (gate), 14, 15, 16 | rewrites its own policy line, source, operators, meta-skills | the gate, the archive rule, the budget, the clock, the human on the slow clock |

### What improved, and who approved it

| Lesson | The file that improved | Who approved it |
|---|---|---|
| 01 regular | nothing | nobody - nothing changes |
| 02 loop | nothing (`loop.json` is read; the audit log is never read back) | nobody |
| 03 loop writer | a whole loop pack is generated | the human: `y` / `n` / `edit` on the whole pack |
| 04 graph | nothing (`graph.json`, `paths.json` are `mutable: false`) | nobody |
| 05 graph writer | a whole graph pack is generated | the human, after `lint_pack`; `edit` lands the human's graph |
| 06 RSI harness | `memory.json` (cards) | the verifier contract, written by the human |
| 07 proof | `memory.json` over problems 1-6; nothing on the exam | the evaluator is frozen: split, metric, seeds |
| 08 RSI writer | actor + verifier packs generated | the human approves the verifier contract explicitly |
| 09 meta harness | `SKILL.md` policy line, `schema.json` forbid, `memory.json` | the human (`approval: human`) or the private gate (`approval: gate`); `versions/` + rollback |
| 10 Dream-RSI | `SKILL.md` policy line, chosen by replay at zero fits | the human; the policy library is fixed |
| 11 RSIAgent | `plan.json` per phase; `memory.json` after `score_test` only | the uncertainty rule; memory frozen at test |
| 12 ModularRSI | one of `modules/*.md` | the pool's private gate; the allow-list |
| 13 Recuris | one skill card (+ its manifest line) | the validation rule: the value won on this problem |
| 14 DGM lineage | `SKILL.md` and `loop.json` - the harness source | the archive rule, the private gate, then the human |
| 15 AIDE² | `operators.md` (one operator) | the human, then keep-if-better across the set under one budget |
| 16 MetaSkill-Evolve | task skills every problem; `roles/*.md` every k problems | the gate (fast clock); the human (slow clock) |

### The rungs this series refuses to touch

ScienceBuddy (arXiv:2609.17523) runs an inner harness loop and an outer RL
loop that updates the model's weights from the harness's outcomes - the
harness first, then the weights. OpenAI has said in public that automating
AI research is its stated priority. Both are the next rung: the thing that
improves is no longer a file you can `diff` and roll back. Every lesson
here keeps the weights exactly what they were, and the series says so on
every page; that boundary is a choice, not a limitation of the tools.

### Terminology

| Word | What it means here |
|---|---|
| self-refine | a better answer this turn, nothing persists (B0). Lesson 01 with a smarter prompt would still be this. |
| learning | persistent state changes from feedback: `memory.json` after lesson 06. Necessary, not sufficient. |
| self-organise / emergence | structure that nobody wrote appears; nothing in this series claims it. |
| AutoML | a fixed search over a fixed space: lessons 01-05, however fancy the graph. |
| bounded RSI | the loop revises its own state or procedure inside limits a human set: lessons 06-16, every one with an off switch. |
| genuine RSI | closed loops with persistence, transferred and attributed autonomy, verified inheritance under matched budgets - the paper's bar; not reached here, and said so. |

### The acceptance test

A loop in this series is called RSI only when all of these hold, and each
is a test somewhere in `python run_tests.py rsi`:

1. *Structural recursion*: generation n+1 boots what generation n wrote
   (lesson 09's checksums).
2. *Safe inheritance*: every generation is a version, a rejected one is
   rolled back, an archive keeps every variant with its score (09, 14).
3. *Autonomy attribution*: the page says which decision moved and which
   stayed human, and a tool enforces the boundary (`patches:`, `tools.md`,
   the contract).
4. *Reliable verification*: the test split is scored once after FREEZE, the
   private split is the gate's, the exam is never written to, evaluators
   are frozen per epoch (07).
5. *Effective recursion*: the memory arm beats `MEMORY_OFF` under a matched
   budget on the curriculum and on the exam (07's curve and exam).

### Numbers quoted from elsewhere

Every one is *reported*; none was measured here.

- *reported*: the Headroom-Closed Index - advanced mathematics 86.4,
  graduate science 85.8, software engineering 52.6, search / terminal agents
  56.8, tool agents 39.9 (arXiv:2609.11873v2).
- *reported*: Gödel Agent lost ground in 14 % of trials (arXiv:2609.11873v2,
  Challenge 1).
- *reported*: DGM raised SWE-bench 20 -> 50 % with a human-fixed archive and
  parent rule (arXiv:2609.11873v2; arXiv:2505.22954).
- *reported*: A-Evolve-Training 0.80 -> 0.86 over four rounds
  (arXiv:2609.11873v2).
- *reported*: Recuris +32.2 on the longest tasks (arXiv:2608.24876).
- *reported*: AIDE² - seven successive improved versions in 100 outer steps,
  16x context compression (Weco AI tech report, July 2026; code not
  released).
- *reported*: the source tutorial's 162x, 71.97 -> 78.98, 47.57 -> 52.43,
  8xA100 and gpt-6-astra as improver (the source tutorial; not in the papers' abstracts).

Files:

```text
step_17_map/
  run.py          the map as data: LADDER, FILES, TERMS, CURVES, REPORTED; reads every lesson's curve.json
  test_step.py    the claims below
  README.md       this lesson
```

## Governance considerations

- Who approves what: this lesson proposes nothing. The tables are the
  human's reading of the series.
- Off switches: none needed; `run.py` reads files.
- What the model may not do: nothing runs. What this page may not do:
  claim more than the L5 *flavour* - it does not, and the terminology table
  says where the bar is.
- What is and is not self-modified: nothing here. Across the series: files
  (cards, a policy line, a forbid list, module texts, skill cards, the
  harness source, operator texts, role files), each behind a named
  approver; never the model's weights.

## How to measure it

| Claim | Test |
|---|---|
| the ladder places every lesson 00-16 on a rung, with the decision that moved and what stayed human; 09 sits on two rungs | `test_the_ladder_places_every_lesson_on_a_rung` |
| the side-by-side table reads each lesson's `curve.json` and names the lessons not yet run | `test_the_side_by_side_curve_reads_each_lessons_curve_and_names_the_missing` |
| every lesson 01-16 has a file-and-approver row | `test_every_lesson_has_a_file_and_an_approver_row` |
| the six terms are defined, and genuine RSI is marked as not reached | `test_the_six_terms_are_defined` |
| every external number is printed as reported with a source, and every source is cited on this page | `test_every_external_number_is_marked_reported_with_a_source` |

Run `python run_tests.py rsi` from the repo root.

## Next lesson

This is the last lesson. Previous:
[16 - MetaSkill-Evolve](../step_16_rsi_meta_skills/README.md). Back to the
[course page](../README.md).
