# Lesson 08 - A meta skill generates the RSI harness, under human approval

Lesson 05's writer, extended to emit the inner pack **and** the verifier
pack - `memory.json` (empty), `memory.schema.json` (the card type),
`eval.md` (how the pack is judged) and the verifier's `SKILL.md` with the
contract line - from `task.json`. The proposal shows the verifier contract
first, and `lint_pack` refuses a verifier pack without it: the human is
approving the acceptance rule. That is the difference from lessons 03 and
05: the human is not approving a one-off pack but *a mechanism that will
change itself later* - after every problem the verifier will write cards
into the actor's memory, and the actor's next run will obey them. The
README says so, the skill says so to the user, and the recorded transcript
shows the diff the human saw. L1 for the generation; what it generates
runs at L4 (lesson 06); nothing the generated packs learn comes back to the
writer.

## Getting started

Lesson 07 left the proof. This lesson adds `.claude/skills/rsi-writer/`
(`SKILL.md`, `tools.md`, `task.json`, `template/actor/` with six files,
`template/verifier/` with three), mirrored to `.agents/skills/`. Nothing new
under `../tools/`: `apply.py` lands a directory of packs side by side under
`.claude/skills/` without touching the writer, and `propose.py` prints the
contract on top of the diff whenever a payload carries it. Open your agent
in this directory; the generated packs land as `.claude/skills/adult-income/`
and `.claude/skills/adult-income-verifier/` - lesson 07's packs, which you can
then run with lesson 07's curriculum prompt.

## How to execute it

1. Type the prompt:

   ```text
   Use the rsi-writer skill: generate the RSI harness (actor and verifier) for the task in .claude/skills/rsi-writer/task.json and propose it to me.
   ```

   The agent renders both packs into `runs/rsi-writer/rendered/adult-income/`
   and `.../adult-income-verifier/` (nine files) and runs:

   ```bash
   python ../tools/lint_pack.py --pack runs/rsi-writer/rendered --task .claude/skills/rsi-writer/task.json
   python ../tools/propose.py --pack .claude/skills/rsi-writer --task .claude/skills/rsi-writer/task.json --target .claude/skills --kind pack --payload @runs/rsi-writer/rendered --summary "RSI harness for adult_income: actor + verifier, empty memory, the contract"
   ```

2. **You will be asked**, with the contract quoted first and a plain
   sentence about what you are approving. Answer approve / edit / reject;
   the agent then runs
   `python ../tools/apply.py --pack .claude/skills/rsi-writer --task .claude/skills/rsi-writer/task.json --proposal p1 --approved "<your words>"`.
   Strip the contract line from the verifier's `SKILL.md` in an edit and
   the edit is refused: `a verifier pack must state the verifier contract verbatim`.

3. Run what landed: lesson 07's prompt (`Use the adult-income-curriculum
   skill ...`) works here once you also copy lesson 07's
   `adult-income-curriculum` pack, or lesson 06's two-problem prompt as is.
   Reset: `rm -rf runs .claude/skills/adult-income .claude/skills/adult-income-verifier`.
   Headless: `claude -p "<the prompt>"` then `claude -p --continue "approve"`,
   both with `--allowedTools "Bash,Read,Write,Edit,Skill"`. Tests:
   `python run_tests.py rsi`.

## What it looks like

`.claude/skills/rsi-writer/SKILL.md` - step 5 is what makes this lesson
different from lesson 03:

```markdown
---
name: rsi-writer
description: Write the RSI harness for the task in task.json - an actor pack with memory.json, memory.schema.json and eval.md, and a verifier pack with the contract - and propose both for human approval; the user approves a mechanism that will change itself later. Use in rsi/step_08_meta_generates_rsi when a task.json exists and no RSI pack does. You do not fit models.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# RSI writer: a meta skill whose output is a mechanism that will change itself

## Procedure
4. Propose both packs at once. The script prints the verifier contract on top of the diff: it is the acceptance rule the user is approving.
   `python ../tools/propose.py --pack W --task T --target OUT --kind pack --payload @runs/rsi-writer/rendered --summary "RSI harness for <name>: actor + verifier, empty memory, the contract"`
5. Show the user the contract first, then every file of both packs, and say plainly what they are approving: not a one-off pack but a mechanism - the verifier will write cards into the actor's `memory.json` after every problem, and the actor's next run will obey them. Ask: **approve / edit / reject**. Wait; run nothing until the answer arrives.
```

`../tools/_lib/packs.py` - the contract as a constant, and the lint rules a
verifier pack must meet before a human sees it:

```python
VERIFIER_CONTRACT = ("Contract: the verifier sees only {recipe, val_score, error, profile}; "
                     "it never sees the actor's transcript, the test split or the intent.")
```

```python
    if "write_card" in allowed and "memory.schema.json" not in files:
        problems.append("a verifier pack needs memory.schema.json")
    if "write_card" in allowed and VERIFIER_CONTRACT not in body:
        problems.append("a verifier pack must state the verifier contract verbatim")
    if "write_card" in allowed and any(t in allowed for t in ("fit_recipe", "score_test", "walk_path")):
        problems.append("a verifier pack may not fit or score: no one grades their own homework")
```

`../tools/_lib/proposals.py` - a directory of packs lands pack by pack; the
writer next to them is not touched:

```python
def land_pack(target, files):
    """Write the payload under target. One pack replaces target; a directory of packs replaces each sub-pack
    directory and nothing else under target (the writer's own pack lives next to them)."""
    import shutil

    target = Path(target)
    subs = sub_packs(files)
    if subs:
        for sub in subs:
            if (target / sub).exists():
                shutil.rmtree(target / sub)
        packs.write_pack(target, files)
        return {sub: packs.checksums(target / sub) for sub in subs}
```

The recorded run (Claude Code 2.1.278, headless, two turns; the agent's
nine Write calls and its rendering of every file are trimmed):

```text
[Skill rsi-writer]
agent> Following the boot order: tools.md, task.json, then the templates.
$ find .claude/skills/rsi-writer -type f | sort && ls ../tools
[Write runs/rsi-writer/rendered/adult-income/{SKILL.md,tools.md,schema.json,memory.json,memory.schema.json,eval.md}]
[Write runs/rsi-writer/rendered/adult-income-verifier/{SKILL.md,tools.md,memory.schema.json}]
agent> Now the lint.
$ python ../tools/lint_pack.py --pack runs/rsi-writer/rendered --task .claude/skills/rsi-writer/task.json
{"ok": true, "problems": [], ...}
agent> Lint is ok. Now the proposal.
$ python ../tools/propose.py --pack .claude/skills/rsi-writer --task .claude/skills/rsi-writer/task.json --target .claude/skills --kind pack --payload @runs/rsi-writer/rendered --summary "RSI harness for adult_income: actor + verifier, empty memory, the contract"
{"id": "p1", "diff": "### verifier contract (the acceptance rule you are approving)\nContract: the verifier sees only {recipe, val_score, error, profile}; it never sees the actor's transcript, the test split or the intent.\n\n### adult-income-verifier/SKILL.md ...", ...}
agent> Proposal p1 is written; nothing has landed. Lint: ok, 0 problems. Both packs target
.claude/skills/ as adult-income and adult-income-verifier.
## The contract (the acceptance rule you are approving)
> Contract: the verifier sees only {recipe, val_score, error, profile}; it never sees the actor's
> transcript, the test split or the intent.
## What you are approving
Not a one-off pack but a mechanism that changes itself: after every problem's memory arm, the
verifier (adult-income-verifier) reads the fit log, tallies pairs of recipes one field apart, and
writes prefer / forbid / counter cards into the actor's memory.json. The actor's (adult-income) next
run obeys those cards (obey-memory search policy ...). The control arm (--arm control --memory off)
ignores the file and walks the static list, so the two can always be compared under the same 24 fits.
Everything derives from task.json (...); nothing widens it. Memory starts empty ([]).
## The files
### adult-income/ (the actor): SKILL.md ... tools.md ... schema.json (24 recipes ...) memory.json []
memory.schema.json - the card type ... eval.md - how the pack is judged, with 24 fits rendered in
### adult-income-verifier/: SKILL.md (the contract line, the procedure) ... tools.md ... memory.schema.json
approve / edit / reject?
=== user> approve
$ python ../tools/apply.py --pack .claude/skills/rsi-writer --task .claude/skills/rsi-writer/task.json --proposal p1 --approved "approve"
{"id": "p1", "decision": "y", "landed": true, "target": ".claude/skills", "files": ["adult-income-verifier/SKILL.md", "adult-income-verifier/memory.schema.json", "adult-income-verifier/tools.md", "adult-income/SKILL.md", "adult-income/eval.md", "adult-income/memory.json", "adult-income/memory.schema.json", "adult-income/schema.json", "adult-income/tools.md"], "approved_by": "human", "words": "approve"}
agent> Proposal p1 - approved ("approve") - landed. Both packs are now in .claude/skills/:
adult-income/ (SKILL.md, tools.md, schema.json (24 static recipes), memory.json ([]), memory.schema.json,
eval.md) and adult-income-verifier/ (SKILL.md, tools.md, memory.schema.json). apply.py reported
landed: true, 9 files, approved_by: human. The contract in force: (the line above)
[2 turns, 29 s]
```

What to notice: the first thing the user reads is the contract, and the
agent's own summary of what is being approved is the point of the lesson in
one paragraph. The one place the agent tried a shell shortcut (`mkdir` +
`cp` of the template files) was refused by the permission system in
headless mode, and it fell back to its Write tool - the same nine files,
just written by hand.

Files:

```text
step_08_meta_generates_rsi/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/rsi-writer/
│   ├── SKILL.md, tools.md, task.json
│   └── template/
│       ├── actor/      SKILL.md, tools.md, schema.json, memory.json, memory.schema.json, eval.md
│       └── verifier/   SKILL.md (with the contract), tools.md, memory.schema.json
├── .agents/skills/rsi-writer/
├── .claude/skills/adult-income/, adult-income-verifier/   (after approval)
└── runs/rsi-writer/{rendered/, adult_income/proposals/p1.json}
```

## Governance considerations

- **Who approves what.** The human approves the verifier contract and the
  card schema - the acceptance rule under which the actor's memory will
  change from then on - before either exists. `edit` may change the actor's
  procedure or the schema (re-linted); it may not remove the contract.
- **The hook.** Blocks `apply.py` without the user's words.
- **What the script refuses.** A verifier pack without the contract, with a
  fitting tool, or without `memory.schema.json`; a widened budget; the writer
  fitting, scoring or writing a card; `apply.py` without words.
- **What is and is not self-modified.** The writer is not. The packs it
  writes will be (their `memory.json`, by the verifier) - and that is what
  the human is told they are approving. Autonomy attribution (the paper's
  challenge 2): the human approved an improver, not a result.

## How to measure it

| Claim | Test |
|---|---|
| the proposal carries the verifier contract verbatim, first; a proposal without it is refused | `test_proposal_carries_the_contract_and_is_refused_without_it` |
| "no" lands nothing; the writer cannot fit or write a card | `test_no_lands_nothing_and_the_writer_cannot_fit_or_write_a_card` |
| the two packs land side by side without touching the writer, and pass lesson 06's checks (cards written, memory arm >= control on problem 2, forbid cards enforced); nothing comes back to the writer | `test_generated_packs_land_side_by_side_and_pass_lesson_06_checks` |
| the same task twice gives the same proposal | `test_same_task_twice_gives_the_same_proposal` |
| the generated actor's schema and card type equal lesson 07's | `test_generated_actor_equals_lesson_07_actor` |
| the pack contract | `test_pack_contract` |
| the recorded run reproduces (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 09 - the RSI meta harness](../step_09_rsi_meta_harness/README.md): a
pack that patches the pack, under the human and then under a private gate.
Previous: [Lesson 07 - the proof](../step_07_proof/README.md).
