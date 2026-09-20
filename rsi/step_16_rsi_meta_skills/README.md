# Lesson 16 - MetaSkill-Evolve: the improver's skills improve too, slowly

MetaSkill-Evolve (arXiv:2607.05297) runs two timescales on one frozen
model: task skills evolve every problem, meta-skills - the improver's own
procedures - evolve every k problems by the same pipeline, with no extra
model and no extra objective. Here the fast loop is `task-skills-meta`, a
lesson-09 meta pack whose numbers (`Policy flip threshold`, `Cards per
visit`) and order of business live in five role files under `roles/`
(analyzer, retriever, allocator, proposer, evolver), patching the actor's
task skills behind the private gate after every problem. The slow loop is
`meta-evolver`: after problems `k`, `2k`, ... (`k: 3` in its `config.md`)
it reads the same evidence the fast loop reads, judges the fast loop by it,
and proposes one change to one line of one role file - which lands only
with the human's `approve` and is snapshotted under the meta pack's own
`versions/`. This is the "and so on": the pack that patches the pack is
itself a pack with a version history, and its changes are rarer and gated
harder. The paper's L5, with the clock and the human yes on every meta
change staying human.

## Getting started

Prerequisites: lesson 09 (the gate variant is this lesson's fast loop with
its numbers moved into `roles/`). This lesson adds `roles/*.md` to
`task-skills-meta` and the `meta-evolver` pack (`config.md` with `k: 3`,
`approval: human`, `patches: ["roles/*.md"]`).

## How to execute it

1. Open your agent in this directory and type the prompt:

   ```text
   Use the adult-income-curriculum skill with the task-skills-meta fast loop and the meta-evolver slow loop: run the curriculum (problems 1 to 6: control arm, memory arm, verifier, the fast loop under the gate; after problems 3 and 6 the slow loop - show me its diff and ask), print the learning curve, then run the exam over seeds 0 to 4 and print the exam report, and list every fast and slow decision with its version.
   ```

2. After problem 3 and after problem 6 the agent shows a one-line diff of a
   role file (or says there is nothing to change) and asks. Answer
   `approve` (as recorded), `edit: ...` or `reject`.

3. Headless, as recorded (the test continues with `approve` at every
   question):

   ```bash
   claude -p "<the prompt above>" --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   claude -p --continue "approve" --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   ```

4. Tests: `python run_tests.py rsi`. Offline: five roles carrying the
   numbers the fast loop uses; two timescales, two gates (`gate` with
   `patches:` on the actor's task skills; `human` with `patches:` on
   `roles/*.md`); `k: 3`; the meta pack has a version history.
   `RSI_LIVE=1`: every arm scored once; the slow loop's events only on
   `wine` and `synth_shift_b`; every landed role change carries the word
   `approve`; as many `versions/` under `task-skills-meta` as landed changes,
   at most two; curve and exam.

5. To reset: `git checkout -- .claude .agents && rm -rf runs`.

## What it looks like

`.claude/skills/task-skills-meta/roles/allocator.md` and `proposer.md` - the
numbers the fast loop reads:

```markdown
# Role: allocator
Which task skill gets this visit, in order: the policy line, then a forbid, then cards.
Policy flip threshold: 2
```

```markdown
# Role: proposer
One patch per visit. Cards are merged from the last problem's pairs, evidence 1 each.
Cards per visit: 3
```

`.claude/skills/meta-evolver/SKILL.md` - the slow clock and the one change:

```markdown
1. Check the clock: the problem's index must be a multiple of `k`; otherwise say so and stop.
3. Judge the fast loop by that evidence: the number of active cards the last `k` problems added, and whether the memory arm's best val beat the control's on them. Decide ONE change, one file, one line:
   - the fast loop is adding cards but the gap is not growing: raise `Cards per visit` in `roles/proposer.md` by one (it consolidates faster);
   - the actor's policy line is still `static` after `k` problems: lower `Policy flip threshold` in `roles/allocator.md` by one;
   - otherwise nothing: say so and stop.
4. Write the changed role file under `runs/meta-evolver/patch/roles/<file>` (your Write tool) and `propose E T --target task-skills-meta --files runs/meta-evolver/patch --recipe <the last problem's best val recipe> --summary "<role>: <old> -> <new>" --visit <index / k>`. `patches: ["roles/*.md"]`: `propose` refuses any other file. `approval: human`: show the user the diff, ask **approve / edit / reject**, wait, then write their words to `runs/meta-evolver/<task>/proposals/<id>.approved` and `apply E T <id> --approved "<the user's exact words>"`. Nothing lands on a no. Every apply snapshots `M` under `runs/task-skills-meta/versions/gen_NNN/`: the meta pack's version history is a directory you can diff.
```

`.claude/skills/meta-evolver/config.md`:

```markdown
---
meta: "on"
k: 3
---
```

`test_step.py`:

```python
    assert all(r.get("problem", "") in ("", "wine", "synth_shift_b") for r in slow)
    applied = [r for r in slow if r["event"] == "apply"]
    assert all(r["approved"] == "approve" for r in applied)
```

The recorded run (Claude Code 2.1.278, headless; the arms trimmed, the
fast-loop verdicts in one line each, the slow-loop visits in full):

<!-- transcript -->

Files:

```text
step_16_rsi_meta_skills/
├── README.md
├── test_step.py
├── .claude/settings.json
├── .claude/skills/
│   ├── adult-income/                 lesson 09's actor
│   ├── adult-income-verifier/
│   ├── task-skills-meta/             the fast loop: SKILL.md, tools.md, config.md, roles/{analyzer,retriever,allocator,proposer,evolver}.md
│   ├── meta-evolver/                 the slow loop: SKILL.md, tools.md, config.md (k: 3)
│   └── adult-income-curriculum/
├── .agents/skills/                   the same
└── runs/                             (after a run) adult-income/{..., versions/}, task-skills-meta/{helpers/, versions/ (the meta pack's own history)}, meta-evolver/
```

## Governance considerations

- **Who approves what.** Task-skill patches: the private gate, every
  problem. Meta-skill changes: the human, every k problems, one line of one
  role file, with the diff shown. The clock, the judging rule and the
  human yes are fixed.
- **The hook.** `apply` only with `.approved`; the fast loop's `gate` never
  touches `roles/`.
- **What the helper refuses.** The slow loop off the clock; a proposal
  outside `roles/*.md`; the fast loop touching `roles/`, `eval.md` or the
  verifier.
- **What is and is not self-modified.** The actor's task skills (fast,
  gated) and the meta pack's role files (slow, human) - both versioned. The
  slow loop itself, the verifier and the curriculum do not change.
- **Rung.** L5 by the paper's definition (the improver's procedure is
  revised), with a human acceptance rule on every such revision - the page
  claims no more than that.

## How to measure it

| Claim | Test |
|---|---|
| five role files carry the numbers the fast loop reads (`Policy flip threshold: 2`, `Cards per visit: 3`) | `test_five_roles_carry_the_numbers_the_fast_loop_uses` |
| two timescales, two gates; `k: 3`; the slow loop only on the clock and never on the actor; the fast loop never on `roles/` | `test_two_timescales_two_gates` |
| the meta pack's changes are snapshotted under its own `versions/` | `test_meta_pack_has_a_version_history` |
| the pack contract for five packs and the seven intents | `test_front_matter` .. `test_intent_contract` |
| the recorded run: slow-loop events only on problems 3 and 6, landed only on `approve`, one version per landing, at most two; curve and exam (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 17 - the map](../step_17_map/README.md): the ladder, every recorded
curve side by side, and who approved what. Previous:
[lesson 15 - AIDE²](../step_15_rsi_aide2/README.md).
