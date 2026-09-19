# Lesson 09 - The RSI meta harness: a pack that patches the pack, problem by problem

A third pack boots between two problems: `adult-income-meta` reads the whole
trace, the cards and every file of the actor pack, and makes ONE proposal -
the actor's `Search policy:` line, a `schema.json` forbid, or new cards -
with the recipe that motivates it. The proposal goes through the same
approval cycle as a writer's, but now the thing approved is a patch to a
pack that already learns; and the pack ships two modes one line apart:
`approval: human` (every generation's patch is a prompt) and
`approval: gate` (the private split - rows the actor never sees - decides
keep-or-rollback, and the human only reads the log). Every generation is a
snapshot under `versions/`; a rejected patch is rolled back from it. The
recursion is the reboot: generation n+1 boots what generation n wrote, and
the boot checksums in the trace prove it. Under the human this is L4; under
the gate it is the L5 *flavour* - the system revises its own improver's
policy line behind a protected evaluator - and the archive rule and the gate
itself stay human. `META_OFF` is the off switch.

## Getting started

Lesson 08 left the writer. This lesson adds `skills/adult-income-meta/` and
`skills/adult-income-meta-gate/` (identical but for the `approval:` line),
the actor pack of lesson 07 with its policy line set to `static` (the meta
pack's first job is to flip it), and the tools `read_pack`, `patch_pack`,
`private_score` and `rollback`. `common/curriculum.py: meta_visit` boots the
meta pack after each problem; `common/packs.py: snapshot / rollback` are the
version history. This is Stage 5 (Deploy): approval cycles as gates.

## How to execute it

1. Under human approval - you are asked after every problem:

   ```bash
   cd rsi/step_09_rsi_meta_harness
   FAKE_MODEL=1 python run.py --approval human
   FAKE_MODEL=1 HUMAN=script:y,y,y,y,y,y python run.py --approval human   # scripted
   ```

   ```powershell
   cd rsi\step_09_rsi_meta_harness
   $env:FAKE_MODEL = "1"; python run.py --approval human
   ```

   At `approve p1 (patch)? [y/n/edit]` you see a unified diff and the
   evidence recipe: `y` lands it (after a snapshot), `n` lands nothing,
   `edit` lands your `{"files": {...}, "recipe": {...}}`.
2. Under the private gate - no prompt; the log shows each verdict:

   ```bash
   FAKE_MODEL=1 python run.py --approval gate
   ```

3. The off switch: `META_OFF=1 FAKE_MODEL=1 python run.py`. Tests:
   `python run_tests.py rsi`.

## What it looks like

`skills/adult-income-meta/SKILL.md` - the one line that moves a decision:

```markdown
---
name: adult-income-meta
description: Improve the actor pack between two curriculum problems - one patch per visit to its search-policy line, its schema.json forbid list or its memory cards - and put it through the approval cycle. Use after a problem's actor and verifier runs are done, before the next problem boots.
metadata:
  type: workflow
  version: "1.0"
  rsi: "on"
  approval: human
---
```

```markdown
2. Decide ONE change, the first that applies:
   a. The actor's `Search policy:` line says `static` and at least two cards are active: change the line to `obey-memory`.
   b. A field value lost every comparison one field apart it was in, at least three times across the log, and never won: add `{"field": ..., "value": ...}` to `schema.json` -> `forbid`. (`hyper` values are excluded: they belong to one model each.)
   c. Otherwise: the last problem's pairs yield cards the memory does not hold yet; merge at most three of them into `memory.json`.
```

`skills/adult-income-meta-gate/SKILL.md` differs in the front matter only:

```markdown
  approval: gate
```

The actor's line the first generation flips:

`skills/adult-income/SKILL.md`:

```markdown
   Search policy: static
```

The tool: one proposal per visit, a size cap, the test rule kept, a snapshot
before anything lands, and the gate's rollback on a loss:

`../common/tools.py`:

```python
    if run.visits.get("patch_pack", 0) >= 1:
        raise ValueError("one proposal per visit; this visit already made one")
```

```python
    if changed_chars > SIZE_CAP * total:
        raise ValueError(f"the patch changes {changed_chars} of {total} characters, more than {int(SIZE_CAP * 100)} % of the pack; one small change per generation")
    if "SKILL.md" in changes and changes["SKILL.md"]["after"] and "after FREEZE" not in changes["SKILL.md"]["after"]:
        raise ValueError("a patch may not remove the test rule from SKILL.md")
```

```python
    if mode == "gate":
        # the private gate: snapshot, land, score the evidence recipe on the private split; a loss rolls back
        label = land_patch(run, payload)
        verdict = private_gate(run, rec)
```

```python
def private_gate(run, candidate):
    """Keep-or-rollback on the private split: the candidate recipe must not score below the incumbent."""
    before = tasks.score_on(run.task, run.seed, incumbent_recipe(run), "private")
    after = tasks.score_on(run.task, run.seed, candidate, "private")
    keep = after is not None and (before is None or after >= before)
```

Expected output, on this machine (`FAKE_MODEL=1 HUMAN=script:y,y,y,y,y,y
--approval human`; the first prompt is shown, the rest elided):

```text
--- proposal p1: patch - search policy: obey the cards (>= 2 active)
--- a/SKILL.md
+++ b/SKILL.md
@@ -18,3 +18,3 @@
-   Search policy: static
+   Search policy: obey-memory
(evidence recipe: {"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "balanced"})
--- end of proposal
...
 # problem                 mem val  ctl val     gap  mem test  ctl test wasted m/c cards +/-/act
 1 adult_income             0.9172   0.9172 +0.0000    0.9034    0.9034   16/16      4/0/4
 2 breast_cancer            0.9966   0.9954 +0.0012    0.9883    0.9844    0/0       3/0/7
 3 wine                        1.0      1.0 +0.0000       1.0       1.0    0/0       0/0/7
 4 digits                    0.999    0.999 +0.0000    0.9984    0.9984    0/0       3/1/9
 5 synth_shift_a            0.9531   0.9507 +0.0024    0.9178    0.9181    1/0       4/1/12
 6 synth_shift_b            0.8571   0.7925 +0.0646    0.9104     0.834    2/17      2/2/13
  after problem 1: adult-income-meta -> {"id": "p1", "decision": "y", "gate": null, "landed": true, "version": "gen_001"}
  after problem 2: adult-income-meta -> null
  after problem 3: adult-income-meta -> null
  after problem 4: adult-income-meta -> null
  after problem 5: adult-income-meta -> {"id": "p1", "decision": "y", "gate": null, "landed": true, "version": "gen_002"}
  after problem 6: adult-income-meta -> null
versions: ['gen_001', 'gen_002']; actor pack byte-identical to skills/: False
actor boots (checksums of SKILL.md / schema.json / memory.json per generation):
  adult_income     a8161f196126 fe416aeb708b 37517e5f3dc6
  breast_cancer    cdd2d3f39422 fe416aeb708b 66d72d59372c
  wine             cdd2d3f39422 fe416aeb708b cf17a31704bc
  digits           cdd2d3f39422 fe416aeb708b cf17a31704bc
  synth_shift_a    cdd2d3f39422 fe416aeb708b f455c8ffb4e0
  synth_shift_b    cdd2d3f39422 fe416aeb708b 4cf3925c8ac1
```

Read the last block: `SKILL.md` changes once (generation 1 flipped the
policy line, and every later problem booted that text), `schema.json` never
(no value lost every comparison it was in), `memory.json` on every problem
the verifier learned something. `null` after a problem means the meta pack
found nothing to propose and said so. Under `--approval gate` the same two
patches land with `"gate": {"before": 0.8951, "after": 0.8951, "keep":
true}` and `{"before": 0.9395, "after": 0.9395, "keep": true}`: the evidence
recipe of a policy patch is the incumbent itself, so the gate holds. With
`META_OFF=1` every line reads `META_OFF`, `versions: none`, and the curve
is lesson 07's for problem 1 and flat after it: the actor never learned to
obey its cards.

Files:

```text
step_09_rsi_meta_harness/
  skills/adult-income/            lesson 07's actor with `Search policy: static` and an empty forbid list
  skills/adult-income-verifier/   lesson 07's verifier
  skills/adult-income-meta/
    SKILL.md                      read log, cards, pack; one change (policy line | forbid | cards); patch_pack
    tools.md                      Allowed: read_traces, read_memory, read_pack, patch_pack, private_score, rollback
  skills/adult-income-meta-gate/  the same pack with `approval: gate`
  run.py                          --approval human | gate; META_OFF; prints the curve, the generations, the boot checksums
  test_step.py                    the claims below
  README.md                       this lesson
  runs/curriculum_<mode>/         (created by run.py) traces.jsonl, curve.json, versions/gen_NNN/ with CHECKSUMS.json
```

## Governance considerations

- Who approves what: under `approval: human`, the human approves every
  patch (a diff and the evidence recipe) - the acceptance rule is the human,
  L4. Under `approval: gate`, the private split approves patches and the
  human reads the log - the system revises its own improver's policy line,
  the L5 flavour. What stays human in both: the gate itself (which split,
  which comparison), the archive rule (every generation kept, restore by
  label), the verifier contract, the size cap, the curriculum and the exam.
- Off switches: `META_OFF` (no meta visit; the pack's fixed files stay
  byte-identical); `n` at any prompt; `rollback` to any `gen_NNN`.
- What the model may not do, and which tool enforces it: fit or score the
  test split (`tools.md`; `execute`); a second proposal per visit
  (`patch_pack`); a patch over 20 % of the pack or one that drops the test
  rule (`patch_pack`); write cards directly (`write_card` is not in its
  `tools.md`: cards go through the versioned, approved patch); look at the
  private split more than twice per visit (`private_score`).
- What is and is not self-modified: the actor's `SKILL.md` policy line,
  `schema.json` forbid list and `memory.json` are. The meta pack itself,
  the verifier, `eval.md` and the tools are not - lesson 16 is where the
  improver's own files move, on a slower clock. Attribution: the model
  chose the patch and, under the gate, decided to keep it; the human chose
  what a patch may touch and what "better" means.

## How to measure it

| Claim | Test |
|---|---|
| generation n+1 boots the files generation n wrote (boot checksums equal the apply checksums; `versions/gen_001` holds the old text) | `test_generation_n_plus_1_boots_the_files_generation_n_wrote` |
| under `approval: human` no patch lands without a `y` | `test_under_human_approval_nothing_lands_without_a_y` |
| under `approval: human` an `edit` lands the human's version | `test_under_human_approval_an_edit_lands_the_humans_version` |
| under `approval: gate` a patch that raises val and lowers `private_score` is rejected and `versions/` restores the previous pack; a second proposal per visit is refused | `test_under_the_gate_a_patch_that_raises_val_and_lowers_private_is_rejected_and_rolled_back` |
| under `approval: gate` a patch that holds on the private split lands, and the verdict is in the log | `test_under_the_gate_a_patch_that_holds_on_private_lands` |
| `META_OFF` leaves the pack byte-identical (its fixed files) and makes no version | `test_meta_off_leaves_the_pack_byte_identical` |
| the meta pack cannot call `score_test`, `fit_recipe` or `write_card`; both meta packs lint | `test_the_meta_pack_cannot_call_score_test_or_fit` |

Scorecard fields reported: all fourteen per problem and arm, plus per
generation the meta visit's answer (`landed`, `version`, the gate verdict).
Run `python run_tests.py rsi` from the repo root.

## Next lesson

Next: [10 - Dream-RSI](../step_10_rsi_dream/README.md): rank search
policies on the trace log with zero fits. Previous:
[08 - a meta skill generates the RSI harness](../step_08_meta_generates_rsi/README.md).
