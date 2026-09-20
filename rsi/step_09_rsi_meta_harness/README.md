# Lesson 09 - The RSI meta harness: a pack that patches the pack, problem by problem

Lesson 06's verifier wrote cards. This lesson adds a pack that patches the
*pack*: between two curriculum problems the meta pack reads the log, the
cards and the actor's files, decides ONE change by a fixed rule - flip the
actor's `Search policy:` line from `static` to `obey-memory` once two cards
are active; else add a `forbid` to `schema.json` for a value that lost
every comparison; else merge up to three fresh cards - and proposes it as a
patch under a 20 % cap that may never remove the test rule. Two modes on
disk. `adult-income-meta` (`approval: human`): the diff is shown, the human
answers approve / edit / reject, nothing lands without their words. Its
twin `adult-income-meta-gate` (`approval: gate`): the patch lands, the
evidence recipe is scored against the incumbent on a *private* split no
actor arm ever sees, and the helper keeps or rolls back; the human reads the
log afterwards. Every patch is snapshotted first under
`runs/adult-income/versions/gen_NNN/`, so `rollback` can undo it, and the
curriculum skill re-reads the actor's `SKILL.md` before every memory arm:
generation n+1 boots what generation n wrote, which is the recursion. Under
the human this is L4; under the gate the system revises its own improver's
policy line behind a protected evaluator - the paper's L5 *flavour*, and no
more: the rule, the cap, the archive and the gate itself stay human.

## Getting started

Prerequisites: lesson 07 (the curriculum, `eval.md`, the verifier) and
lesson 03 (`propose` / `apply`). This lesson ships the actor with
`Search policy: static` (lesson 06's actor obeyed memory from the start;
here the meta pack has to earn it), the two meta packs (`SKILL.md`,
`tools.md`, `config.md` with `meta: on`), and the curriculum skill with a
meta visit after every problem. Two recordings: the gate over the whole
curriculum, and the human visit on problem 1.

## How to execute it

1. Under the gate, open your agent in this directory and type:

   ```text
   Use the adult-income-curriculum skill with the adult-income-meta-gate meta pack: run the curriculum (problems 1 to 6: control arm, memory arm, verifier, then the meta visit under the gate), print the learning curve, then run the exam over seeds 0 to 4 and print the exam report, and list every meta decision with its version.
   ```

   Nobody is asked. After each problem the meta pack proposes at most one
   patch, `gate` snapshots the actor, lands it, scores evidence against
   incumbent on the private split and keeps or rolls back.

2. Under the human, on one problem:

   ```text
   Use the adult-income-curriculum skill with the adult-income-meta meta pack on problem 1 only: control arm, memory arm, verifier, then the meta visit under human approval - propose the patch and ask me.
   ```

   The agent shows the diff (the policy line flipped to `obey-memory`, if
   the verifier wrote two active cards) and asks. Answer `approve` (as
   recorded), `edit: ...` or `reject`.

3. Headless, as recorded:

   ```bash
   claude -p "<the gate prompt>" --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   claude -p "<the human prompt>" --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   claude -p --continue "approve" --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   ```

4. Tests: `python run_tests.py rsi`. Offline: the actor ships `static` with
   one patchable line; the two meta packs differ only in who decides (the
   rule is identical text); one change per visit under the cap; the
   curriculum re-reads the actor before every memory arm; the gate contract
   uses the private split only. `RSI_LIVE=1`: the gate run leaves every
   curriculum arm frozen and scored once, `gen_NNN` versions on disk, `gate`
   events with a keep / rollback decision, `curve.json`, `exam.json` with
   `pack_unchanged`; the human run leaves a proposal and no version until
   `approve`, then `gen_001` and the words in the trace.

5. To reset: restore the packs (`git checkout -- .claude .agents`) and
   `rm -rf runs`.

## What it looks like

`.claude/skills/adult-income-meta/SKILL.md` - the front matter carries the
mode and the files it may touch; the rule is one change per visit:

```markdown
---
name: adult-income-meta
description: "Improve the actor pack adult-income between two curriculum problems - one patch per visit to its Search policy line, its schema.json forbid list or its memory cards - and put it through the human approval cycle (approve / edit / reject). Use in rsi/step_09_rsi_meta_harness after a problem's actor and verifier runs are done, before the next problem boots."
metadata:
  type: workflow
  version: "3.0"
  rsi: "on"
  approval: human
  patches: ["SKILL.md", "schema.json", "memory.json"]
---
# The RSI meta harness: a pack that patches the pack

## Procedure
2. Decide ONE change, the first that applies:
   a. The actor's `Search policy:` line says `static` and at least two cards are active: change that line to `Search policy: obey-memory` (the whole `SKILL.md`, with that one line changed).
   b. A field value lost every comparison one field apart it was in, at least three times across the whole log, and never won: add `{"field": ..., "value": ...}` to `schema.json -> forbid` (`hyper` values are excluded: they belong to one model each).
   c. Otherwise: the last problem's pairs yield cards the memory does not hold yet (`read_traces P T --scope problem --tally` lists `cards_by_rule`); merge at most three of them into `memory.json`.
   If none applies, say so and stop: nothing is proposed this visit.
4. Show the user the diff and ask: **approve / edit / reject**. Wait; run nothing until the answer arrives. ...
```

`.claude/skills/adult-income-meta-gate/SKILL.md` - the same rule, the other
landing:

```markdown
4. `gate M T <id>`: the helper snapshots the actor pack under `runs/adult-income/versions/gen_NNN/`, lands the patch, scores the evidence recipe against the incumbent (the best val recipe of the newest problem in the log) on the private split - a split no actor arm ever sees - and keeps the patch only if it did not score lower; otherwise it restores the snapshot. It prints `decision`, `before`, `after`, `keep`, `landed`.
5. Answer in text with the proposal id, the gate's numbers, whether it landed and the version label. Nobody is asked: under `approval: gate` the human reads the log (`runs/adult-income-meta-gate/<task>/traces.jsonl`) and may run `rollback adult-income gen_NNN` afterwards. Stop.
```

`.claude/skills/adult-income-meta-gate/tools.md` - the gate and the private
split:

```markdown
- `gate(pack, task, id, seed=0)` - the private gate, for a pack whose front matter says `approval: gate` (or `both`): snapshot the target under `runs/<target name>/versions/gen_NNN/`, land the proposal's files, then `private_score` the proposal's evidence recipe and the incumbent (the best val recipe of the newest problem in the target's log); keep the patch only if the evidence recipe did not score lower, else restore the snapshot. Append `{"event": "gate", "id", "before", "after", "keep", "version"}` and print `decision` (`keep` | `rollback`), the two scores and `landed`. Nobody is asked.
- `private_score(pack, task, recipe, seed=0)` - the recipe fitted on train and scored on the private part of the split; costs no budget and touches no state; refuse for an actor pack (only a meta pack may see the private part, and no arm's `score_test` ever does).
```

`.claude/skills/adult-income/SKILL.md` - the one line a meta pack may patch:

```markdown
3. Search, until a result says `FREEZE`, under the policy the line below names - the one line of this file a meta pack may patch:
   Search policy: static
```

`test_step.py` - the two meta packs share the rule word for word:

```python
    rule = lambda body: section(body, "Procedure").split("2. Decide")[1].split("3. Write")[0]
    assert rule(human[1]) == rule(gate[1])
```

The recorded run under the gate (Claude Code 2.1.278, headless; the arms
trimmed to their scorecards, the meta visits in full):

<!-- transcript -->

Files:

```text
step_09_rsi_meta_harness/
├── README.md
├── test_step.py
├── .claude/
│   ├── settings.json
│   └── skills/
│       ├── adult-income/                 the actor, Search policy: static, eval.md
│       ├── adult-income-verifier/
│       ├── adult-income-meta/            approval: human - propose, show, wait, apply with the words
│       │   ├── SKILL.md  tools.md  config.md (meta: on)
│       ├── adult-income-meta-gate/       approval: gate - propose, gate (private split), keep or rollback
│       │   ├── SKILL.md  tools.md  config.md
│       └── adult-income-curriculum/      actor -> verifier -> meta visit, per problem; re-reads the actor's SKILL.md
├── .agents/skills/                       the same five packs
└── runs/                                 (after a run) adult-income/{..., versions/gen_NNN/}, adult-income-meta*/{helpers/, patch/, <task>/{proposals/, traces.jsonl}}
```

## Governance considerations

- **Who approves what.** Under `approval: human`, every patch: the diff,
  the words, the trace. Under `approval: gate`, nobody per patch - the
  private split decides - and the human reads the log and may roll back.
  In both modes the human wrote the rule (a / b / c), the cap (20 %, the
  test rule untouchable), the `patches:` list and the gate; those are not
  the system's to change.
- **The hook.** `score_test` after `"frozen": true`; `apply` only with an
  `.approved` file. The gate helper is named `gate`, not `apply`, on
  purpose: the hook's second rule is about the human's words, and the gate
  has none.
- **What the helper refuses.** `propose`: a second proposal in a visit, a
  file outside `patches:`, more than 20 % of the pack, a patch that removes
  the test rule, a patched pack that does not lint. `private_score`: any
  actor pack. `score_test` is forbidden to both meta packs and absent from
  their procedures.
- **What is and is not self-modified.** The actor's `SKILL.md` (one line),
  `schema.json` (the `forbid` list) and `memory.json` - and every change is
  a `gen_NNN` snapshot away from undone. The meta packs, the verifier,
  `eval.md` and the curriculum never change. `meta: off` in `config.md`
  (META_OFF) leaves the actor byte-identical between problems.
- **Rung.** L4 under the human; L5 flavour under the gate, because the
  policy line that governs the improver's own search is revised behind a
  protected evaluator. Not more: the archive rule and the gate stay human,
  and the page says so.

## How to measure it

| Claim | Test |
|---|---|
| the actor ships `Search policy: static`, exactly one patchable line, both policies described, versions named | `test_actor_ships_static_with_one_patchable_line` |
| the two meta packs differ only in who decides: same rule text, same `patches:`, `apply` vs `gate`, `config.md` with `meta` | `test_two_meta_packs_differ_only_in_who_decides` |
| one change per visit, the 20 % cap, the test rule untouchable | `test_the_rule_is_one_change_per_visit_under_a_cap` |
| the curriculum re-reads the actor before every memory arm and lists versions | `test_curriculum_reboots_the_patched_actor` |
| the gate keeps only a non-lower private score and refuses actors | `test_gate_contract_uses_the_private_split_only` |
| the pack contract for five packs | `test_front_matter` .. `test_no_python_shipped` |
| the recorded runs: the gate curriculum (arms scored once, versions, gate events, curve, exam unchanged) and the human visit (no version until `approve`, then `gen_001` and the words) (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 10 - Dream-RSI](../step_10_rsi_dream/README.md): rank the search
policies on the log at zero fits, and propose the winner as the policy line.
Previous: [lesson 08 - a meta skill generates the RSI harness](../step_08_meta_generates_rsi/README.md).
