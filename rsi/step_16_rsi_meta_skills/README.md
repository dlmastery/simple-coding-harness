# Lesson 16 - MetaSkill-Evolve: the improver's skills improve too, slowly

MetaSkill-Evolve (arXiv:2607.05297) runs two timescales on one frozen
model: task skills evolve every problem, meta-skills every k problems, by
the same pipeline, with no extra model or objective. Here the fast loop
(`task-skills-meta`) is lesson 09's meta pack under the gate, but its
procedure's numbers live in five role files - `roles/analyzer.md`,
`retriever.md`, `allocator.md` (`Policy flip threshold: 2`), `proposer.md`
(`Cards per visit: 3`), `evolver.md` - and only the slow loop
(`meta-evolver`, `approval: human`, `patches: ["roles/*.md"]`, `k` in its
`config.json`) may change one line of one of them, every `k` problems, with
the human's word. The fast loop's own version history is a directory you can
diff (`runs/task-skills-meta/versions/`). This is the "and so on": the pack
that patches the pack is itself a pack with a version history, and its
changes are rarer and gated harder. L5 with the human on the slow clock.

## Getting started

Lesson 09's actor, verifier and curriculum skill; the fast loop from lesson
09's gate pack with `roles/`; the new slow loop with `config.json`
`{"k": 3}`. No new script: `patch_pack.py` with `patches: ["roles/*.md"]`
and the no-self-patch rule (a pack does not patch itself) is all it takes.
Reset: `git checkout -- .claude/skills`, mirror, `rm -rf runs`.

## How to execute it

1. Type the prompt:

   ```text
   Use the adult-income-curriculum skill: run the six curriculum problems with task-skills-meta after each and meta-evolver every k problems, then the exam, and report the curve, the exam, the fast decisions and the slow decisions.
   ```

   **You will be asked** on problems 3 and 6 (k = 3), when the slow loop
   proposes one role line, for example:

   ```bash
   python ../tools/patch_pack.py --pack .claude/skills/meta-evolver --task ../tasks/03_wine.json --target .claude/skills/task-skills-meta --files @runs/meta-evolver/patch --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=none --summary "proposer: Cards per visit 3 -> 4" --visit 1
   python ../tools/patch_pack.py --pack .claude/skills/meta-evolver --task ../tasks/03_wine.json --target .claude/skills/task-skills-meta --proposal g1 --approved "<your words>"
   ```

   Answer approve / edit / reject; nothing lands on a no. The fast loop's
   own visits go through the gate without asking.

2. By hand: the fast loop cannot patch its own `roles/` (`a pack does not
   patch itself`), the slow loop cannot patch the actor (`may patch
   ['roles/*.md'] only`), and `meta-evolver` off the clock proposes nothing.

3. Headless: `claude -p "<the prompt>"` and `claude -p --continue "<your
   answer>"` at each slow visit, all with `--allowedTools
   "Bash,Read,Write,Edit,Skill"`. Tests: `python run_tests.py rsi`.

## What it looks like

`.claude/skills/task-skills-meta/roles/proposer.md` and `roles/allocator.md`
- the numbers the fast loop uses are lines in files:

```markdown
# Role: proposer
One patch per visit. Cards are merged from the last problem's pairs, evidence 1 each.
Cards per visit: 3
```

```markdown
# Role: allocator
Which task skill gets this visit, in order: the policy line, then a forbid, then cards.
Policy flip threshold: 2
```

`.claude/skills/meta-evolver/SKILL.md` - the slow loop:

```markdown
---
name: meta-evolver
description: The slow loop of MetaSkill-Evolve - every k problems, propose one change to one meta-skill file (roles/*.md) of the task-skills-meta pack, by the same evidence pipeline, and land it only with the human's approval. Use in rsi/step_16_rsi_meta_skills on the slow clock (k in config.json), never after every problem.
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
  approval: human
  patches: ["roles/*.md"]
---
# The slow loop: the improver's own skills, rarely, with a human

## Procedure
1. Check the clock: the problem's index must be a multiple of `k`; otherwise say so and stop.
3. Judge the fast loop by that evidence: the number of active cards the last `k` problems added, and whether the memory arm's best val beat the control's on them. Decide ONE change, one file, one line:
   - the fast loop is adding cards but the gap is not growing: raise `Cards per visit` in `roles/proposer.md` by one (it consolidates faster);
   - the actor's policy line is still `static` after `k` problems: lower `Policy flip threshold` in `roles/allocator.md` by one;
   - otherwise nothing: say so and stop.
```

`../tools/patch_pack.py` - a pack does not patch itself, and a meta pack
patches only what its front matter allows:

```python
    if Path(target).resolve() == run.pack_dir:
        raise ValueError("a pack does not patch itself: the target is another pack (the actor, or the fast loop's pack)")
```

```python
        if allowed and not any(fnmatch(name, pat) for pat in allowed):
            raise ValueError(f"this meta pack may patch {allowed} only, not {name}")
```

RECORDING_16

Files:

```text
step_16_rsi_meta_skills/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/adult-income/, adult-income-verifier/, adult-income-curriculum/
├── .claude/skills/task-skills-meta/          SKILL.md (approval: gate), tools.md, roles/{analyzer,retriever,allocator,proposer,evolver}.md
├── .claude/skills/meta-evolver/              SKILL.md (approval: human, patches: roles/*.md), tools.md, config.json {"k": 3}
└── .agents/skills/...
```

## Governance considerations

- **Who approves what.** The gate approves task-skill patches every
  problem; the human approves meta-skill patches every `k` problems, one
  line of one role file. The clock (`k`) and the role files' shape are the
  human's.
- **The hook.** Blocks the slow loop's second `patch_pack.py` call without
  the user's words; the locked test as always.
- **What the script refuses.** The fast loop patching `roles/` (not in its
  `patches:`) or itself; the slow loop patching the actor; a proposal off
  the clock (the skill), a landing without words (the hook and the script).
- **What is and is not self-modified.** The actor's task skills (fast), the
  fast loop's role files (slow). The slow loop's own `SKILL.md`, the clock
  and the human are not.

## How to measure it

| Claim | Test |
|---|---|
| task skills change every problem and meta-skills only on the slow clock (counted from the versions and traces); the curve stays non-negative | `test_two_timescales_counted_from_the_traces` |
| a meta-skill change never lands without the human's yes; an edit or a yes lands one role line; the fast loop's version history is a directory you can diff | `test_meta_skill_change_never_lands_without_the_human` |
| the fast loop cannot touch `roles/` and the slow loop cannot touch the actor or fit | `test_fast_loop_cannot_touch_roles_and_slow_loop_cannot_touch_the_actor` |
| the fast loop boots what the slow loop wrote | `test_fast_loop_boots_what_the_slow_loop_wrote` |
| the pack contract | `test_pack_contract` |
| the recorded run reproduces (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 17 - the map](../step_17_map/README.md). Previous:
[Lesson 15 - AIDE²](../step_15_rsi_aide2/README.md).
