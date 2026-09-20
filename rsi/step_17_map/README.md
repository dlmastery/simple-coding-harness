# Lesson 17 - The map: the ladder, every recorded curve side by side, and who approved what

You recognise the nouns because you built the toy. The last skill,
`rsi-map`, changes nothing and runs no lesson: its one helper reads every
lesson directory's `runs/<pack>/curve.json` and `exam.json` where they
exist and prints them side by side around the text of `ladder.md` - the
paper's ladder (arXiv:2609.11873) with lessons 00-16 placed on their rungs
and what stayed human on each; the file-and-approver table (which file each
method changed, and who said yes); the six terms (self-refine, learning,
self-organise, AutoML, bounded, genuine); and every number quoted from a
paper, each marked *reported* with its source. A lesson without a recorded
curve is printed as `not run yet`, never invented, and the map does not run
a curriculum to fill the gap. The series ends on the sentence the map
prints last: genuine RSI by the paper's bar - closed loops with persistence,
transferred and attributed autonomy, verified inheritance under matched
budgets, domain-appropriate feedback infrastructure - is not reached here,
and every lesson said which rung it stands on instead.

## Getting started

Prerequisites: whichever lessons you ran; the map reads their `runs/`. This
lesson adds `rsi-map` (`SKILL.md`, `tools.md` with the `map` contract,
`ladder.md`).

## How to execute it

1. Open your agent in this directory and type the prompt:

   ```text
   Use the rsi-map skill: print the map of the series from the runs that exist and report.
   ```

2. No approval; nothing changes.

3. Headless, as the live test runs it:

   ```bash
   claude -p "Use the rsi-map skill: print the map of the series from the runs that exist and report." \
     --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   ```

4. Tests: `python run_tests.py rsi`. Offline: `ladder.md` places every
   lesson, marks its reported numbers and names the six terms; the skill and
   the contract never invent a curve. `RSI_LIVE=1`: the lesson directory
   unchanged, every lesson with a recorded curve named in the report,
   `reported` and `not reached` in the text.

## What it looks like

`.claude/skills/rsi-map/ladder.md` - the ladder:

```markdown
| Rung | Lessons | The decision the system takes | What stays human |
|---|---|---|---|
| L1 precondition | 00 intent | none | what to improve, how, success |
| not RSI (B0 / AutoML / harness engineering) | 01 regular, 02 loop, 04 graph | none: a fixed procedure | everything |
| L1 | 03, 05, 08 (the writers) | executes a generation procedure | the intent, the acceptance (approve / edit / reject) |
| L4 | 06 RSI harness, 07 proof, 09 (approval: human), 11 RSIAgent, 13 Recuris | revises persistent state (cards, plan, skill cards) from run feedback | the verifier contract, the schema, the off switch |
| L2 | 10 Dream-RSI | chooses the search strategy from replay | the policy library |
| L2 -> L5 flavour | 12 ModularRSI | patches one harness module off-benchmark | the module boundaries, the pool |
| L4 -> L5 flavour | 09 (approval: gate), 14 DGM lineage, 15 AIDE2 | revises the improver's policy line / its own source / its operators behind a protected evaluator | the archive rule, the gate, the meter, the task set |
| L5 | 16 MetaSkill-Evolve | revises its own meta-skills on a slow clock | the clock, the human yes on every meta change |
```

`.claude/skills/rsi-map/tools.md` - the one contract:

```markdown
- `map(lessons)` - read each lesson directory's `runs/<pack>/curve.json` and `exam.json` where they exist and print: the ladder (rung, lessons, the decision the system takes, what stays human), the learning curves side by side (a lesson without a curve is `not run yet`, never invented), the file-and-approver table, the six terms, and the numbers quoted from papers - each marked *reported* with its source. Costs no fit; changes no file.
```

The recorded run (not yet recorded on this machine; the weekly usage cap was reached
after lesson 16's recording - the block below says how to produce it, and the curves it
will read are the ones lessons 07, 09, 10, 11, 13, 15 and 16 left under their `runs/`):

```text
Recording pending - this lesson's transcript has not been recorded yet.
Run it here to produce it (about a minute in Claude Code; the live test records the run
under runs/_recording/ and asserts on the artifacts):

    RSI_LIVE=1 python -m pytest -q test_step.py -k live -s

Nothing above is invented: the pack, the contracts and the tests are complete, and the
"What to notice" paragraph will be written from the recording.
```

Files:

```text
step_17_map/
├── README.md
├── test_step.py
├── .claude/settings.json
├── .claude/skills/rsi-map/           SKILL.md, tools.md (map), ladder.md
├── .agents/skills/rsi-map/           the same
└── runs/rsi-map/helpers/             (after a run)
```

## Governance considerations

- **Who approves what.** Nobody; nothing changes. The map is a reader.
- **The hook.** Installed for the shape; nothing to block.
- **What the helper refuses.** To invent: a lesson without a curve is
  `not run yet`.
- **What is and is not self-modified.** Nothing.
- **The claim.** The series claims L5 *flavour* at most, and the map's last
  sentence says genuine RSI is not reached here.

## How to measure it

| Claim | Test |
|---|---|
| `ladder.md` places every lesson, marks every external number *reported*, names the six terms and says genuine RSI is not reached | `test_ladder_places_every_lesson_and_marks_reported_numbers` |
| the skill and the contract never invent a curve or run a lesson | `test_map_never_invents_a_curve` |
| the pack contract | `test_front_matter` .. `test_no_python_shipped` |
| the recorded run: nothing changed, every recorded lesson named, `reported` and `not reached` in the text (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

None: this is the last. The [course page](../README.md) lists them all.
Previous: [lesson 16 - MetaSkill-Evolve](../step_16_rsi_meta_skills/README.md).
