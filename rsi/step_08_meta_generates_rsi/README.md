# Lesson 08 - A meta skill generates the RSI harness, under human approval

The writer of lesson 05, extended once more: `rsi-writer` emits two packs
from `task.json` - the actor with `memory.json`, `memory.schema.json` and
`eval.md`, and the verifier with its contract - lints both, and proposes
them together. What the human approves this time is not a one-off pack but
a *mechanism that will change itself later*: the verifier will write cards
into the actor's `memory.json` on every problem, without asking. So the
proposal puts the verifier contract first, `lint_pack` refuses a verifier
without it (or one that can fit), and the writer's summary says the pack
will change its own memory. The framework paper's attribution challenge in
one prompt: the human is approving an improver, not a result. Generation is
L1; what it generates runs at L4.

## Getting started

Lesson 07 left the actor pack with `eval.md` and the verifier. This lesson
adds `skills/rsi-writer/` with a `template/actor/` and a
`template/verifier/` directory (lesson 07's packs with placeholders; the
card schema is rendered from `{{card_schema}}` into both), the multi-pack
lint in `common/packs.py`, and the contract line at the top of the approval
prompt (`common/approve.py: show`). The landed packs go to
`runs/generated/rsi/{actor,verifier}/`.

## How to execute it

1. Generate, read the contract, decide, then watch the generated packs
   learn across two problems:

   ```bash
   cd rsi/step_08_meta_generates_rsi
   FAKE_MODEL=1 python run.py
   ```

   ```powershell
   cd rsi\step_08_meta_generates_rsi
   $env:FAKE_MODEL = "1"; python run.py
   ```

   At `approve p1 (pack)? [y/n/edit]` you are approving the contract and
   both packs: `y` lands them, `n` lands nothing, `edit` lands your version
   (an edit that drops the contract is refused by `lint_pack` when it is
   proposed again). Scripted: `HUMAN=script:y`.
2. Tests: `python run_tests.py rsi`.

## What it looks like

`skills/rsi-writer/SKILL.md`:

```markdown
---
name: rsi-writer
description: Write the RSI harness for the task in task.json - an actor pack with memory.json, memory.schema.json and eval.md, and a verifier pack with the contract - and propose both for human approval. Use when a task.json exists and no RSI pack does. You do not fit models.
metadata:
  type: workflow
  version: "1.0"
  rsi: "off"
---
# RSI writer: a meta skill whose output is a mechanism that will change itself
```

```markdown
2. Render both template directories: `{{name}}`, `{{slug}}`, `{{title}}`, `{{n_fits}}`, `{{models}}`, `{{test_rule}}`, `{{recipes}}` (the static list of the allowed models), `{{card_schema}}` (the JSON Schema of a card, identical in both packs). The verifier's SKILL.md keeps its contract line word for word: it is the acceptance rule of the mechanism, and `lint_pack` refuses a verifier without it.
```

The contract, and the two lint rules that hold a verifier to it:

`../common/packs.py`:

```python
VERIFIER_CONTRACT = ("Contract: the verifier sees only {recipe, val_score, error, profile}; "
                     "it never sees the actor's transcript, the test split or the intent.")
```

```python
    if "write_card" in allowed and VERIFIER_CONTRACT not in body:
        problems.append("a verifier pack must state the verifier contract verbatim")
    if "write_card" in allowed and any(t in allowed for t in ("fit_recipe", "score_test", "walk_path")):
        problems.append("a verifier pack may not fit or score: no one grades their own homework")
```

What the human sees first:

`../common/approve.py`:

```python
        if any(VERIFIER_CONTRACT in text for text in payload.values()):
            print(f"### verifier contract (the acceptance rule you are approving)\n{VERIFIER_CONTRACT}", file=out)
```

Expected output, on this machine (`FAKE_MODEL=1 HUMAN=script:y`; the
files of the proposal are elided):

```text
--- proposal p1: pack - a pack for adult_income from the template; this pack will change its own memory.json on every problem it runs
### verifier contract (the acceptance rule you are approving)
Contract: the verifier sees only {recipe, val_score, error, profile}; it never sees the actor's transcript, the test split or the intent.
### actor/SKILL.md
...
--- end of proposal
Proposal p1 decided y: applied p1 (y) to rsi.
lint of the landed packs: ok
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 breast_cancer            0.9954   0.9954 +0.0000    0.9844    0.9844    0/0       1/0/1
 2 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834    3/17      3/0/4
```

The generated packs are lesson 07's packs with the task's values filled in,
so they learn what lesson 06's did: after one problem of evidence, the
second problem's memory arm ends 0.065 higher on validation and 0.076 higher
on the locked test, reaching the static grid's best in 3 fits instead of 17.

Files:

```text
step_08_meta_generates_rsi/
  skills/rsi-writer/
    SKILL.md                      read the task, render two packs, lint both, propose, apply if approved
    tools.md                      Allowed: read_task, lint_pack, propose, apply
    task.json                     the intent of lesson 00
    template/actor/SKILL.md       lesson 07's actor with {{slug}}, {{title}}, {{n_fits}}
    template/actor/tools.md       lesson 07's actor tools
    template/actor/schema.json    {{name}}, {{n_fits}}, {{test_rule}}, {{models}}, {{recipes}}; forbid []
    template/actor/memory.schema.json  {{card_schema}}
    template/actor/memory.json    []
    template/actor/eval.md        lesson 07's eval.md
    template/verifier/SKILL.md    lesson 07's verifier, the contract line verbatim
    template/verifier/tools.md    read_traces, write_card
    template/verifier/memory.schema.json  {{card_schema}}
  run.py                          generate -> approve -> run both packs over two problems
  test_step.py                    the claims below
  README.md                       this lesson
```

## Governance considerations

- Who approves what: the human approves the verifier contract explicitly
  (it is printed first), and both packs. After that, cards land under the
  contract without a prompt - that is the decision being delegated, and the
  summary says so.
- Off switches: `n`; `MEMORY_OFF` on the generated actor.
- What the model may not do, and which tool enforces it: the writer may not
  fit, score or read a trace (`tools.md`, `execute`); it may not propose a
  verifier without the contract or with a fitting tool (`propose` ->
  `lint_pack`); the generated actor may not write cards; the generated
  verifier may not fit (lesson 06's tools).
- What is and is not self-modified: the writer never changes; the generated
  actor's `memory.json` changes on every problem it runs; nothing flows back
  to the writer. Rung: L1 for the generation, L4 for what it generates.

## How to measure it

| Claim | Test |
|---|---|
| the proposal contains the verifier contract verbatim, the human sees it first, the summary names the self-change, `n` lands nothing | `test_proposal_contains_the_verifier_contract_and_the_human_sees_it_first` |
| `lint_pack` refuses a proposal whose verifier lacks the contract or can fit, before the human is asked | `test_lint_refuses_a_proposal_without_the_contract` |
| the generated packs pass lesson 06's checks: isolation, the word test refused, `MEMORY_OFF` = lesson 01, memory >= control | `test_generated_packs_pass_step_06_checks` |
| generating twice gives the same proposal; the writer has no budget | `test_generating_twice_gives_the_same_proposal` |

Scorecard fields reported by the generated packs' runs: all fourteen. Run
`python run_tests.py rsi` from the repo root.

## Next lesson

Next: [09 - the RSI meta harness](../step_09_rsi_meta_harness/README.md):
a pack that patches the pack, under human approval and then under a private
gate. Previous: [07 - proof](../step_07_proof/README.md).
