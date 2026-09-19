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

MAP_TABLE

RECORDING_17

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
