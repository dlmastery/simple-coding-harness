# Lesson 03 - A meta skill generates the loop harness, under human approval

The first meta harness: a pack whose output is another pack. `loop-writer`
boots with `task.json` and five template files, renders lesson 02's pack
from the task, lints it, and proposes it. The harness shows the whole pack;
the human answers `y`, `n` or `edit`; only then does anything land, and an
`edit` lands the human's text, not the model's. This is rung L1 of the
framework paper: humans specify what, how and success; the system executes a
generation procedure; a human accepts. Two facts keep it below RSI:
generating twice from the same `task.json` gives byte-identical proposals,
and running the generated pack never changes it or reaches back to the
writer. Most "an agent built an agent" demos stop exactly here.

## Getting started

Lesson 02 left the loop pack and `lint_pack`'s loop checks. This lesson adds
`skills/loop-writer/` (a pack with a `template/` directory), three tools
(`read_task`, `lint_pack`, `propose`, `apply` - never `fit_recipe`) and the
approval cycle in `common/approve.py`. The generated pack lands under
`runs/generated/adult-income-loop/`.

## How to execute it

1. Generate, approve at the prompt, then watch the generated pack run on
   Adult:

   ```bash
   cd rsi/step_03_meta_generates_loop
   FAKE_MODEL=1 python run.py
   ```

   ```powershell
   cd rsi\step_03_meta_generates_loop
   $env:FAKE_MODEL = "1"; python run.py
   ```

   At `approve p1 (pack)? [y/n/edit]` answer `y` to land the pack as
   proposed, `n` to land nothing, or `edit` and paste the edited `{path:
   text}` JSON on one line to land your version instead.
2. Scripted answers for a run without a terminal: `HUMAN=script:y` (or
   `script:n`). Tests: `python run_tests.py rsi`.

## What it looks like

`skills/loop-writer/SKILL.md` - a writer that never fits:

```markdown
---
name: loop-writer
description: Write a loop harness pack (SKILL.md, tools.md, schema.json, loop.json, recipes.json) for the task in task.json and propose it for human approval. Use when a task.json exists and no loop pack does. You do not fit models.
metadata:
  type: workflow
  version: "1.0"
  rsi: "off"
---
# Loop writer: a meta skill whose output is a loop harness

## Boot order
1. This file. 2. `tools.md`. 3. `task.json`: what to improve, the metric, the budget, the allowed models, the test rule. 4. `template/*`: the shape of every file you emit.
```

`skills/loop-writer/tools.md`:

```markdown
## Allowed
- read_task - the task.json this writer was booted for
- lint_pack - the generated pack, linted against the task and booted dry
- propose - show the pack to the human and get y / n / edit
- apply - land an approved proposal

## Forbidden
- fit_recipe, score_test, save_model - the writer never trains anything
```

`skills/loop-writer/template/loop.json` carries the budget as a placeholder the
writer fills from the task - it cannot pick its own:

```json
 "kind": "counted_while",
 "N": {{n_fits}},
 "counter": "t",
```

The approval cycle: a proposal is decided the moment it is made, and applied
only on request, only if approved.

`../common/approve.py`:

```python
    def propose(self, kind, payload, summary=""):
        pid = f"p{len(self.items) + 1}"
        proposal = {"id": pid, "kind": kind, "payload": payload, "summary": summary, "decision": None, "applied": False}
        self.items[pid] = proposal
        if not self.quiet:
            show(proposal)
        decision, edited = self.human.decide(proposal)
        proposal["decision"] = decision
        if decision == "edit":
            proposal["payload"] = edited     # the human's version is what may land
        return proposal
```

`../common/tools.py`:

```python
@tool("apply", id="string")
def apply(run, id):
    """Land an approved proposal on the target pack. Refuses one the human answered n to, or never saw."""
    if not run.proposals.approved(id):
        raise ValueError(f"proposal {id} is not approved; nothing lands")
```

Expected output, on this machine (`FAKE_MODEL=1 HUMAN=script:y`; the
proposal itself - every file - is printed between the `--- proposal p1` and
`--- end of proposal` lines and is elided here):

```text
--- proposal p1: pack - a pack for adult_income from the template
### SKILL.md
---
name: adult-income-loop
description: Train a classifier for Adult Census Income (> 50k) by running the counted loop in loop.json over recipes.json. Generated from task.json by loop-writer.
...
--- end of proposal
Proposal p1 decided y: applied p1 (y) to adult-income-loop.
lint of the landed pack: ok
adult_income [control] fits 24/24 wasted 16 best val 0.9172 test 0.9034 recipe {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"}
generated pack byte-identical after its run: True
```

The generated pack gives lesson 02's numbers exactly: it is lesson 02's pack
with the task's values filled in.

Files:

```text
step_03_meta_generates_loop/
  skills/loop-writer/
    SKILL.md              read the task, render the template, lint, propose, apply if approved
    tools.md              Allowed: read_task, lint_pack, propose, apply
    task.json             the intent of lesson 00
    template/SKILL.md     lesson 02's SKILL.md with {{name}}, {{title}}, {{metric}}, {{n_fits}} placeholders
    template/tools.md     lesson 02's tools.md
    template/schema.json  {{name}}, {{metric}}, {{n_fits}}, {{test_rule}}, {{models}}
    template/loop.json    lesson 02's loop with N = {{n_fits}}
    template/recipes.json {{recipes}}
  run.py                  generate -> approve -> run the generated pack on Adult
  test_step.py            the claims below
  README.md               this lesson
  runs/generated/         (created by run.py) adult-income-loop/, the landed pack
```

## Governance considerations

- Who approves what: the human approves the whole pack, file by file, before
  it exists on disk. `n` means nothing lands; `edit` means the human's text
  lands. The writer's `task.json` is the human's too.
- Off switches: answer `n`. Scripted humans default to `n` when their
  answers run out.
- What the model may not do, and which tool enforces it: fit anything
  (`fit_recipe` is not in `tools.md`; `execute` refuses it); propose a pack
  that widens the task (`propose` runs `lint_pack` first and refuses before
  the human is asked); land an unapproved proposal (`apply` refuses).
- What is and is not self-modified: the writer changes nothing about
  itself; the generated pack changes nothing about itself when it runs;
  nothing the generated pack does reaches the writer. Rung: L1.

## How to measure it

| Claim | Test |
|---|---|
| the writer cannot call `fit_recipe` (not in its `tools.md` -> `Error:`) | `test_writer_cannot_fit` |
| the proposal is shown before anything lands; scripted `n` leaves the disk untouched | `test_proposal_is_shown_before_anything_lands_and_n_lands_nothing` |
| `y` lands exactly the proposal | `test_y_lands_exactly_the_proposal` |
| `edit` lands the human's text | `test_edit_lands_the_humans_text` |
| generating twice from the same `task.json` gives byte-identical proposals | `test_generating_twice_gives_byte_identical_proposals` |
| the generated pack boots, passes lesson 02's checks, and running it changes none of its files | `test_generated_pack_boots_and_passes_step_02_checks` |

Scorecard fields reported by the generated pack's run: all fourteen. Run
`python run_tests.py rsi` from the repo root.

## Next lesson

Next: [04 - graph engineering with loops](../step_04_graph_harness/README.md).
Previous: [02 - loop engineering](../step_02_loop_harness/README.md).
