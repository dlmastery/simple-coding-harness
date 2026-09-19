# Lesson 03 - A meta skill generates the loop harness, under human approval

The first "agent builds agent": a writer skill that never fits a model
reads `task.json`, renders lesson 02's pack from a template (five files), lints
it against the task, and proposes it. The human sees every file and answers
approve / edit / reject; `n` means nothing lands, `edit` means the human's
version lands, and the trace records who approved and with which words. It
is one shot from a spec - the same `task.json` gives the same proposal, and
running the generated pack never changes it - so this is where most "agent
builds agent" demos stop: L1 in the framework paper's terms (humans specify
what, how and success; the system executes a generation procedure; the human
accepts). Not RSI yet: nothing the generated pack learns comes back to the
writer.

## Getting started

Lesson 02 left the loop pack; this lesson generates it instead. It adds
`.claude/skills/loop-writer/` (`SKILL.md`, `tools.md`, `task.json`,
`template/` with the five files as templates) and two scripts,
`../tools/propose.py` and `../tools/apply.py` - the approval cycle every
"generate" and every "improve" in the series goes through. Open your agent
in this directory. The generated pack lands at `.claude/skills/adult-income-loop/`
(not shipped: you make it); `runs/` holds the proposal and the rendered
scratch files.

## How to execute it

1. Type the prompt:

   ```text
   Use the loop-writer skill: generate the loop pack for the task in .claude/skills/loop-writer/task.json and propose it to me.
   ```

   The agent reads the task and the templates, writes the five rendered
   files with its own Write tool into `runs/loop-writer/rendered/`, then runs:

   ```bash
   python ../tools/lint_pack.py --pack runs/loop-writer/rendered --task .claude/skills/loop-writer/task.json
   python ../tools/propose.py --pack .claude/skills/loop-writer --task .claude/skills/loop-writer/task.json --target .claude/skills/adult-income-loop --kind pack --payload @runs/loop-writer/rendered --summary "loop pack for adult_income: 24 static recipes, counted loop"
   ```

2. **You will be asked.** The agent shows all five files and asks
   "approve / edit / reject". Answer in your own words - the first word
   decides: `yes` / `approve` / `ok` lands it; `edit` followed by what to
   change lands your version; `no` / `reject` records a rejection and lands
   nothing. Only then does the agent run:

   ```bash
   python ../tools/apply.py --pack .claude/skills/loop-writer --task .claude/skills/loop-writer/task.json --proposal p1 --approved "approve"
   ```

   (or `--approved "edit" --edited @runs/loop-writer/edited`). Without
   `--approved` the hook blocks the call and the script refuses it.

3. Run what landed: `Use the adult-income-loop skill ...` as in lesson 02; the
   numbers are lesson 02's. Reset with `rm -rf runs .claude/skills/adult-income-loop`.

4. Headless, as recorded below, in two turns:
   `claude -p "<the prompt>" --allowedTools "Bash,Read,Write,Edit,Skill"` then
   `claude -p --continue "approve" --allowedTools "Bash,Read,Write,Edit,Skill"`.
   PowerShell: `--payload '@runs/loop-writer/rendered'` (quote the `@`).
   Tests: `python run_tests.py rsi`.

## What it looks like

`.claude/skills/loop-writer/SKILL.md` - the writer's procedure. Step 5 is the
approval question; step 6 lands "exactly what was decided":

```markdown
---
name: loop-writer
description: Write a loop harness pack (SKILL.md, tools.md, schema.json, loop.json, recipes.json) for the task in task.json and propose it for human approval; nothing lands until the user answers. Use in rsi/step_03_meta_generates_loop when a task.json exists and no loop pack does. You do not fit models.
metadata:
  type: workflow
  version: "2.0"
  rsi: "off"
---
# Loop writer: a meta skill whose output is a loop harness

## Procedure
1. Read `W/task.json`. Everything you write derives from it; nothing you write may widen it.
2. Render the five template files into a scratch directory, `runs/loop-writer/rendered/` (create it; use your Write tool), replacing each `{{placeholder}}` from the task and nothing else:
3. Lint what you rendered, and fix it until `ok` is true; propose nothing that does not lint:
   `python ../tools/lint_pack.py --pack runs/loop-writer/rendered --task W/task.json`
4. Propose it. The script lints again, writes the proposal under `runs/loop-writer/<task>/proposals/` and returns its id and the text the user must see:
   `python ../tools/propose.py --pack W --task T --target OUT --kind pack --payload @runs/loop-writer/rendered --summary "loop pack for <name>: 24 static recipes, counted loop"`
5. Show the user every file of the proposal (the `diff` field), then ask, in your own words but with these three options: **approve / edit / reject**. Wait for the answer. Do not run anything until it arrives.
6. Land exactly what was decided, quoting the user's words verbatim:
   - approve: `python ../tools/apply.py --pack W --task T --proposal <id> --approved "<the user's exact words>"`
```

`.claude/skills/loop-writer/template/loop.json` - a template is the target
file with `{{placeholders}}`; the writer may fill them and nothing else:

```json
{
 "kind": "counted_while",
 "N": {{n_fits}},
 "counter": "t",
 "error_still_counts": true,
 "body": [
  "recipe = recipes[t]",
  "fit_recipe.py --recipe recipe  (or --recipes @recipes.json --range t:t+6)",
  "write_loop_log.py {t, recipe, val_score}"
 ],
 "exit": ["FREEZE", "score_test", "save_model", "scorecard"]
}
```

`../tools/_lib/proposals.py` - the user's words decide, by their first word,
and anything unclear is a no:

```python
YES = ("y", "yes", "approve", "approved", "ok", "okay", "lgtm", "go", "ship", "accept", "accepted", "apply", "land", "sure")
NO = ("n", "no", "reject", "rejected", "nope", "deny", "denied", "stop", "cancel", "decline")
EDIT = ("edit", "edited", "change", "modify")


def classify(words):
    """The user's words -> y / n / edit, by the first word. Anything unclear is a no: nothing lands by default."""
    first = re.sub(r"[^a-z]", "", (words or "").strip().lower().split(" ")[0]) if words and words.strip() else ""
    if first in EDIT:
        return "edit"
    if first in YES:
        return "y"
    if first in NO:
        return "n"
    return "n"
```

`../tools/apply.py` - refuses without the words, records a rejection, lints
an edited pack before it lands, applies at most once:

```python
    if a.approved is None or not a.approved.strip():
        raise ValueError('apply needs --approved "<the user\'s exact words>": ask them first; nothing lands without an answer')
    path, record = proposals.load(run.root, a.proposal)
    if record["applied"]:
        raise ValueError(f"proposal {a.proposal} was applied already")
    if record["decision"] == "n":
        raise ValueError(f"proposal {a.proposal} was rejected already; propose again if you have something new")
    decision = proposals.classify(a.approved)
    record["decision"], record["words"], record["approved_by"] = decision, a.approved, "human"
```

`../tools/propose.py` - a pack that does not lint is refused before the user
ever sees it:

```python
    if a.kind == "pack":
        if not isinstance(payload, dict) or not all(isinstance(v, str) for v in payload.values()):
            raise ValueError("a pack payload is {path: text}")
        problems = lint_payload(payload, run.task)
        if problems:
            raise ValueError(f"lint_pack refuses this pack before the user sees it: {problems}")
```

The recorded run (Claude Code 2.1.278, headless, two turns; the agent's
rendering of the five files omitted - it is lesson 02's pack with
`adult_income` filled in):

```text
[Skill loop-writer]
agent> Using the loop-writer skill. Boot order: tools.md, task.json, templates.
[Read .claude/skills/loop-writer/task.json]  [Read template/SKILL.md] [Read template/loop.json] ...
agent> Now rendering the five files. The 24 recipes: models in allowed_models order at their
middle hyper, then scale yes/no, encode onehot/ordinal, class_weight none/balanced.
[Write runs/loop-writer/rendered/SKILL.md] [Write runs/loop-writer/rendered/loop.json]
[Write runs/loop-writer/rendered/recipes.json] [Write runs/loop-writer/rendered/schema.json]
[Write runs/loop-writer/rendered/tools.md]
$ python ../tools/lint_pack.py --pack runs/loop-writer/rendered --task .claude/skills/loop-writer/task.json
{"ok": true, "problems": [], "pack": "runs/loop-writer/rendered", "task": "adult_income"}
agent> Lint is clean. Proposing.
$ python ../tools/propose.py --pack .claude/skills/loop-writer --task .claude/skills/loop-writer/task.json --target .claude/skills/adult-income-loop --kind pack --payload @runs/loop-writer/rendered --summary "loop pack for adult_income: 24 static recipes, counted loop"
{"id": "p1", "kind": "pack", "target": ".claude/skills/adult-income-loop", "diff": "### SKILL.md\n---\nname: adult-income-loop ...",
 "next": "Show the diff to the user. Ask: approve / edit / reject. Then: python ../tools/apply.py ... --approved \"<the user's exact words>\""}
agent> Proposal p1 is written (lint: ok: true, 0 problems) - loop pack for adult_income: 24 static
recipes, counted loop - targeting .claude/skills/adult-income-loop. Nothing has landed yet.
Here are all five files of the proposal:
### SKILL.md  (name: adult-income-loop ... `t` reached `N` (24) ...)
### loop.json ("N": 24 ...)   ### recipes.json (24 recipes)   ### schema.json   ### tools.md
Every value comes from task.json (name, title, metric roc_auc, budget 24, models logreg/rf/hgb,
test rule 1 score after FREEZE); the templates were filled and nothing was added.
How do you want to proceed with proposal p1?
- approve - I land it as-is at .claude/skills/adult-income-loop
- edit - tell me what to change; I write your version and land that
- reject - nothing lands, the rejection is recorded
I'll wait for your answer before running anything.
[20 turns, 124 s]
=== user> approve
$ python ../tools/apply.py --pack .claude/skills/loop-writer --task .claude/skills/loop-writer/task.json --proposal p1 --approved "approve"
{"id": "p1", "decision": "y", "landed": true, "target": ".claude/skills/adult-income-loop", "version": null,
 "files": ["SKILL.md", "loop.json", "recipes.json", "schema.json", "tools.md"], "approved_by": "human", "words": "approve"}
agent> Proposal p1 - decision: approved (your words: "approve") - landed.
What landed at .claude/skills/adult-income-loop/: SKILL.md, loop.json, recipes.json, schema.json, tools.md.
```

What to notice: the agent stopped and waited - in headless mode the answer
came as a second `claude -p --continue "approve"` turn, and `apply.py`
carries those words into the trace (`"by": "human", "words": "approve"`).
The landed pack equals the reference rendering file for file except that
the agent's `recipes.json` is formatted one recipe per line where the
reference indents it - same 24 recipes, same order; `lint_pack` checks the
content, and the test's "same task twice, byte-identical" claim is about
the script's determinism given the same payload.

Files:

```text
step_03_meta_generates_loop/
├── README.md
├── test_step.py
├── .claude/settings.json
├── .claude/skills/loop-writer/
│   ├── SKILL.md, tools.md
│   ├── task.json                   the spec (a copy of ../tasks/01_adult_income.json)
│   └── template/                   SKILL.md, tools.md, schema.json, loop.json, recipes.json with {{placeholders}}
├── .agents/skills/loop-writer/     the same files
├── .claude/skills/adult-income-loop/   (after approval: the generated pack)
└── runs/loop-writer/
    ├── rendered/                   the agent's rendering (scratch)
    └── adult_income/
        ├── proposals/p1.json, p1.diff
        └── traces.jsonl            propose, then apply {by: human, words: "approve"}
```

## Governance considerations

- **Who approves what.** The human approves the whole pack, file by file,
  before it exists on disk; `edit` lands the human's text, not the model's.
  The writer decides nothing about the task: every value in the pack comes
  from `task.json`, and `lint_pack` refuses a pack that widens it.
- **The hook.** Blocks `apply.py` without `--approved "<words>"` (exit 2,
  "show the proposal and ask first").
- **What the script refuses.** `fit_recipe.py` / `score_test.py` for the
  writer (`not in loop-writer's tools.md`); a proposal that does not lint;
  `apply.py` without words, twice, or after a rejection; an edited pack that
  does not lint.
- **What is and is not self-modified.** Nothing modifies itself. The writer
  writes a *different* pack, once, and never sees its runs; the generated
  pack changes no file when it runs (asserted). Autonomy attribution: the
  system executed a generation procedure the human specified; the human
  accepted. That is L1.

## How to measure it

| Claim | Test |
|---|---|
| the writer cannot fit or score (its `tools.md` does not allow it; the scripts refuse) | `test_writer_cannot_fit` |
| the rendered pack lints; the proposal shows every file before anything lands | `test_rendered_pack_lints_and_the_proposal_is_shown_before_anything_lands` |
| "no" leaves the disk untouched, and the proposal cannot be revived | `test_no_leaves_the_disk_untouched` |
| "yes" lands exactly the proposal, once, with the human's words in the trace | `test_yes_lands_exactly_the_proposal` |
| "edit" lands the human's text; an edit that widens the budget does not lint and does not land | `test_edit_lands_the_humans_text` |
| the same task twice gives byte-identical proposals | `test_same_task_twice_gives_byte_identical_proposals` |
| the generated pack passes lesson 02's checks and is unchanged by its run; nothing comes back to the writer | `test_generated_pack_runs_like_lesson_02_and_is_unchanged_by_its_run` |
| `apply` without the words is refused by the script and blocked by the hook | `test_apply_without_words_is_refused_and_blocked` |
| the pack contract | `test_pack_contract` |
| the recorded run reproduces (`RSI_LIVE=1`) | `test_live_claude_code` |

Scorecard: none of its own - the generated pack reports lesson 02's.

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 04 - graph engineering with loops](../step_04_graph_harness/README.md):
the job as a DAG, a recipe as a path. Previous:
[Lesson 02 - loop engineering](../step_02_loop_harness/README.md).
