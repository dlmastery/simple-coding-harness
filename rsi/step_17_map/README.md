# Lesson 17 - The map: the ladder, every recorded curve side by side, and who approved what

You recognise the nouns because you built the toy. This lesson is one
script and one skill: `map.py` prints the ladder of the framework paper
(arXiv:2609.11873) with lessons 00-16 placed on their rungs - the decision
the system takes and what stays human - then every lesson's learning curve
on the same curriculum side by side, read from the `curve.json` its
curriculum skill left (a lesson not run is named, never invented), then the
file-by-file table of what improved and who approved it, the six terms this
series uses on purpose, and every number quoted from elsewhere marked
*reported* with its source. ScienceBuddy (arXiv:2609.17523, harness then
weights) and OpenAI's stated priority are the rungs this series refuses to
touch: no weight update anywhere, and "genuine RSI" by the paper's bar is
not reached here - the map says so.

## Getting started

The series is done; this lesson reads it. `.claude/skills/rsi-map/`
(`SKILL.md`, `tools.md`) and `../tools/map.py`. The curves come from the
other lessons' `runs/` directories; run lesson 07 (and 09-16) first to fill
the table, or read it with the gaps named.

## How to execute it

1. Type the prompt:

   ```text
   Use the rsi-map skill: print the map and tell me which lessons have a recorded curve.
   ```

   The agent runs one command:

   ```bash
   python ../tools/map.py --lessons ..
   ```

   (`--section ladder | curves | files | terms | reported` for one part.)
   No approval, nothing changes, nothing is run.

2. Headless: `claude -p "<the prompt>" --allowedTools "Bash,Read,Write,Edit,Skill"`.
   Tests: `python run_tests.py rsi`.

## What it looks like

`.claude/skills/rsi-map/SKILL.md`:

```markdown
---
name: rsi-map
description: Print the map of the rsi series - the ladder of rungs with lessons 00-16 placed, every recorded learning curve on the same curriculum side by side, the file-and-approver table, the terminology, and every external number marked reported - from the runs that exist. Use in rsi/step_17_map.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# The map: you recognise the nouns because you built the toy

## Rules
- Print the numbers the script prints; every external number is *reported*, none is measured here.
- Do not run a lesson's curriculum to fill a gap in the table: say it is not run yet.
```

`../tools/map.py` - the ladder, and the rule that a missing curve is named:

```python
LADDER = [
    ("not RSI (B0 / AutoML / harness engineering)", ["01", "02", "04"], "none: a fixed procedure", "everything"),
    ("L1  what to improve, how, success - specified by humans; AI executes a generation procedure", ["00", "03", "05", "08"], "renders a pack from task.json", "the spec, the acceptance (y / n / edit), the verifier contract"),
    ("L2  how to improve: the search strategy", ["10", "12"], "ranks policies on the log; names the module to patch", "the policy library, the module boundaries, the pool"),
    ("L3  which experience to acquire", ["11"], "picks the next experiments by uncertainty", "the uncertainty rule, the phase lengths"),
    ("L4  revise persistent state from deployment feedback under an acceptance rule", ["06", "07", "09 (human)", "13"], "writes and demotes cards; one patch per generation", "the verifier contract, the off switches, the human at the prompt"),
    ("L5 flavour  revise the improver / verifier / successor procedure itself", ["09 (gate)", "14", "15", "16"], "rewrites its own policy line, source, operators, meta-skills", "the gate, the archive rule, the budget, the clock, the human on the slow clock"),
]
```

```python
        if curve is None:
            lines.append(f"  {label:<18}  not run yet (run that lesson's curriculum skill)")
            continue
```

The map on this machine, after the recorded runs of this series (the
`table` field of `map.py`):

```text
The ladder (arXiv:2609.11873): rung | lessons | the decision the system takes | what stays human
  not RSI (B0 / AutoML / harness engineering)
      lessons 01, 02, 04 | none: a fixed procedure | everything
  L1  what to improve, how, success - specified by humans; AI executes a generation procedure
      lessons 00, 03, 05, 08 | renders a pack from task.json | the spec, the acceptance (y / n / edit), the verifier contract
  L2  how to improve: the search strategy
      lessons 10, 12 | ranks policies on the log; names the module to patch | the policy library, the module boundaries, the pool
  L3  which experience to acquire
      lessons 11 | picks the next experiments by uncertainty | the uncertainty rule, the phase lengths
  L4  revise persistent state from deployment feedback under an acceptance rule
      lessons 06, 07, 09 (human), 13 | writes and demotes cards; one patch per generation | the verifier contract, the off switches, the human at the prompt
  L5 flavour  revise the improver / verifier / successor procedure itself
      lessons 09 (gate), 14, 15, 16 | rewrites its own policy line, source, operators, meta-skills | the gate, the archive rule, the budget, the clock, the human on the slow clock
Learning curves on the same curriculum (memory arm - control arm, best val, per problem):
  lesson               adult_income  breast_cancer           wine         digits  synth_shift_a  synth_shift_b  wasted m/c
  07 proof                  +0.0000        +0.0012        +0.0000        +0.0000        +0.0024        +0.0646       20/33
  09 meta (gate)            +0.0000        +0.0012        +0.0000        +0.0000        +0.0024        +0.0646       20/33
  10 Dream-RSI              +0.0000        +0.0012        +0.0000        +0.0005        +0.0024        +0.0646       34/33
  11 RSIAgent               +0.0000        +0.0000        +0.0000        +0.0000        +0.0000        -0.0270       27/33
  13 Recuris                +0.0000        +0.0000        +0.0000        +0.0000        +0.0024        +0.0646        6/33
  16 MetaSkill              +0.0000        +0.0012        +0.0000        +0.0000        +0.0024        +0.0646       20/33
What improved, and who approved it:
  01 regular           nothing                                                                nobody (nothing changes)
  02 loop              nothing (loop.json is read, the audit log is never read back)          nobody
  03 loop writer       a whole loop pack is generated                                         the human: y / n / edit on the whole pack
  04 graph             nothing (graph.json and paths.json are mutable: false)                 nobody
  05 graph writer      a whole graph pack is generated                                        the human, after lint_pack; edit lands the human's graph
  06 RSI harness       memory.json (cards)                                                    the verifier contract, written by the human
  07 proof             memory.json over problems 1-6; nothing on the exam                     the evaluator is frozen: split, metric, seeds
  08 RSI writer        actor + verifier packs generated                                       the human approves the verifier contract explicitly
  09 meta harness      SKILL.md policy line, schema.json forbid, memory.json                  the human (approval: human) or the private gate (approval: gate); versions/ + rollback.py
  10 Dream-RSI         SKILL.md policy line, chosen by replay at zero fits                    the private gate; the policy library is fixed
  11 RSIAgent          plan.json per phase; memory.json after score_test only                 the uncertainty rule; memory frozen at test
  12 ModularRSI        one of modules/*.md                                                    the pool's private gate; the allow-list
  13 Recuris           one skill card (+ its manifest line)                                   the validation rule: the value won on this problem
  14 DGM lineage       SKILL.md and loop.json (the harness source)                            the archive rule, the private gate, then the human
  15 AIDE2             operators.md (one operator)                                            keep-if-better across the set under one metered budget (meter.py --decide)
  16 MetaSkill-Evolve  task skills every problem; roles/*.md every k problems                 the gate (fast clock); the human (slow clock)
Terminology:
  self-refine                a better answer this turn, nothing persists (B0). Lesson 01 with a smarter prompt would still be this.
  learning                   persistent state changes from feedback: memory.json after lesson 06. Necessary, not sufficient.
  self-organise / emergence  structure that nobody wrote appears; nothing in this series claims it.
  AutoML                     a fixed search over a fixed space: lessons 01-05, however fancy the graph.
  bounded RSI                the loop revises its own state or procedure inside limits a human set: lessons 06-16, every one with an off switch.
  genuine RSI                closed loops with persistence, transferred and attributed autonomy, verified inheritance under matched budgets - the paper's bar; not reached here, and said so.
Numbers quoted from elsewhere (every one *reported*, none measured here):
  reported: Headroom-Closed Index: advanced mathematics 86.4, graduate science 85.8, software engineering 52.6, search / terminal agents 56.8, tool agents 39.9 [arXiv:2609.11873v2]
  reported: Goedel Agent lost ground in 14 % of trials [arXiv:2609.11873v2, Challenge 1]
  reported: DGM raised SWE-bench 20 -> 50 % with a human-fixed archive and parent rule [arXiv:2609.11873v2 / arXiv:2505.22954]
  reported: A-Evolve-Training 0.80 -> 0.86 over four rounds [arXiv:2609.11873v2]
  reported: Recuris +32.2 on the longest tasks [arXiv:2608.24876]
  reported: AIDE2: seven successive improved versions in 100 outer steps, 16x context compression [Weco AI tech report, July 2026; code not released]
  reported: the tutorial's 162x, 71.97 -> 78.98, 47.57 -> 52.43, 8xA100 [the source tutorial; not in the papers' abstracts]
```

The recorded run (Claude Code 2.1.278, headless, 4 turns, 49 s; the table
above is what the script printed):

```text
[Skill rsi-map]
agent> Using the rsi-map skill: running map.py from the lesson directory.
$ python ../tools/map.py --lessons ..
{"ladder": [...], "curves": {...}, "not_run": [], "files": [...], "terms": [...], "reported": [...], "table": "..."}
agent> Six lessons have a recorded curve in runs/<pack>/curve.json: 07 proof, 09 meta (gate), 10 Dream-RSI,
11 RSIAgent, 13 Recuris, and 16 MetaSkill - all six problems present in each, no missing entries, and the
script's not_run list is empty. The remaining lessons (00-06, 08, 12, 14, 15) carry no curve because they
don't run the six-problem curriculum: 00-05 and 08 are generators or fixed procedures with nothing to plot,
and 06, 12, 14, 15 revise cards, modules, harness source or operators rather than producing a
memory-vs-control curve - so nothing there is "not run yet", it is simply not the kind of lesson the curve
table reads. Every figure outside the curve table is reported from its cited source, none measured here.
The series ends on the sentence the map itself states: genuine RSI by the paper's bar - closed loops with
persistence, transferred and attributed autonomy, verified inheritance under matched budgets - is not
reached here, and the map says so.
[4 turns, 49 s]
```

What to notice: the six curves agree on the lessons that share the
`obey-memory` policy flip (07, 09, 16: identical to the fourth decimal), and
differ exactly where the method differs - Dream-RSI's flipping line (34
wasted fits), RSIAgent's uncertainty rule (-0.027 on problem 6), Recuris's
card-first probe (6 wasted fits). `runs/` is git-ignored, so on a fresh
checkout the table names every lesson as not run yet until you run them.

Files:

```text
step_17_map/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/rsi-map/     SKILL.md, tools.md
└── .agents/skills/rsi-map/
```

## Governance considerations

- **Who approves what.** Nobody: the map reads and prints.
- **The hook.** Installed, idle.
- **What the script refuses.** Nothing to refuse; it invents no number - a
  lesson without a `curve.json` is listed as not run.
- **What is and is not self-modified.** Nothing. The acceptance test of the
  whole series is the ladder's last two columns: for every lesson, which
  decision moved to the system, and which stayed human.

## How to measure it

| Claim | Test |
|---|---|
| the ladder places every lesson 00-16 on a rung, with the decision that moved and what stayed human; 09 sits on two rungs | `test_the_ladder_places_every_lesson_on_a_rung` |
| the side-by-side table reads each lesson's `curve.json` and names the lessons not yet run | `test_the_side_by_side_curve_reads_each_lessons_curve_and_names_the_missing` |
| every lesson 01-16 has a file-and-approver row | `test_every_lesson_has_a_file_and_an_approver_row` |
| the six terms are defined, and genuine RSI is marked as not reached | `test_the_six_terms_are_defined` |
| every external number is printed as *reported* with a source, and this page says so | `test_every_external_number_is_marked_reported_with_a_source` |
| the map changes nothing | `test_the_map_changes_nothing` |
| the pack contract | `test_pack_contract` |
| the recorded run reproduces (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

None: this is the map. Previous:
[Lesson 16 - MetaSkill-Evolve](../step_16_rsi_meta_skills/README.md); the
[course page](../README.md) lists them all.
