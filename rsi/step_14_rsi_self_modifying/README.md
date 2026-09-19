# Lesson 14 - The Darwin Gödel Machine lineage: the agent's own source, behind an archive and a gate

The Darwin Gödel Machine (arXiv:2505.22954) keeps an archive of agent
variants with their benchmark scores, picks parents from the archive, and
lets an agent rewrite its own source; the framework paper's verdict on it
(SWE-bench 20 -> 50 %, *reported*) is that the archive and the parent rule
stayed human-fixed - autonomy attribution, not autonomy. This lesson builds
exactly that shape: the meta pack (`dgm-meta`) runs the current actor on a
fixed held-out benchmark (two synthetic tables no curriculum problem
uses), archives the variant with its held-out gain (`archive.py --action
add`), chooses the parent by score - ties to the older, never the latest by
default (`--action parent`, `restore` when it is not the latest) - and
proposes ONE rewrite of the parent's *source*: the `Search policy:` line of
`SKILL.md` and the `policy` field of `loop.json`, the two files `patches:`
allows. `approval: both`: the private gate decides keep-or-rollback first,
then the human sees the diff. A rewrite the gate rejected never runs and
never enters the archive. L5 flavour: the harness source is rewritten; the
archive rule, the gate and the benchmark stay human, and the page says which
files are self-modified and which are not.

## Getting started

Lesson 09's actor with a `loop.json` (its `policy` field mirrors the policy
line), the verifier, and the new `.claude/skills/dgm-meta/` with
`held-out/` (two task files, 1500 rows each). One script: `../tools/archive.py`.
A generation is both arms and the verifier on both held-out tasks, an
archive entry, and a rewrite through the gate and the human (about seven
minutes headless). Reset: `git checkout -- .claude/skills`, mirror, `rm -rf runs`.

## How to execute it

1. Type the prompt:

   ```text
   Use the dgm-meta skill for generation 1: run the current actor on the held-out benchmark, archive it, choose the parent, and propose the rewrite of its source.
   ```

   After the benchmark run the meta pack's own commands are:

   ```bash
   python ../tools/archive.py --pack .claude/skills/dgm-meta --task .claude/skills/dgm-meta/held-out/02_pool_trees_2.json --target .claude/skills/adult-income --action add --label gen1-static --held-out .claude/skills/dgm-meta/held-out --seed 1
   python ../tools/archive.py --pack .claude/skills/dgm-meta --task .claude/skills/dgm-meta/held-out/02_pool_trees_2.json --target .claude/skills/adult-income --action parent
   python ../tools/patch_pack.py --pack .claude/skills/dgm-meta --task .claude/skills/dgm-meta/held-out/02_pool_trees_2.json --target .claude/skills/adult-income --files @runs/dgm-meta/patch --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced --summary "gen2: obey-memory from gen1-static" --visit 1
   ```

2. **You will be asked** after the gate kept the rewrite: approve / edit /
   reject. Then the agent runs
   `python ../tools/patch_pack.py ... --proposal g1 --approved "<your words>"`.
   A "no" rolls the pack back to the snapshot the gate landed on.

3. Generation 2: the same prompt with "generation 2" (`--seed 2`); the
   rewritten pack runs the benchmark, is archived as `gen2-obey-memory`, and
   the parent rule picks between the two by held-out score.

4. Headless: `claude -p "<the prompt>"` then `claude -p --continue "approve"`,
   both with `--allowedTools "Bash,Read,Write,Edit,Skill"`. Tests:
   `python run_tests.py rsi`.

## What it looks like

`.claude/skills/dgm-meta/SKILL.md`:

```markdown
---
name: dgm-meta
description: The Darwin Goedel Machine lineage - rewrite the actor pack's own source (its SKILL.md and loop.json), one generation deep, from a parent chosen in an archive of variants scored on a fixed held-out benchmark, behind the private gate and the human cycle. Use in rsi/step_14_rsi_self_modifying, one generation per visit.
metadata:
  type: workflow
  version: "2.0"
  rsi: "on"
  approval: both
  patches: ["SKILL.md", "loop.json"]
---
# The Darwin Goedel Machine lineage: the agent's own source, with an archive of stepping stones

## Procedure - one generation
3. Choose the parent: `python ../tools/archive.py --pack M --task T --target P --action parent`. The parent is the variant with the best held-out score, ties to the older one; it is not the latest by default. If `is_latest` is false: `python ../tools/archive.py --pack M --task T --target P --action restore --label <parent>`, then `python ../tools/read_pack.py --pack P --checksums`; you now stand on the parent.

## Rules
- One generation deep: a rewrite of the parent, never of a rewrite that has not run the benchmark.
- A variant that lowered the held-out score is in the archive with its score; the parent rule never picks it over a better one. A rewrite the gate rejected never runs and never enters the archive.
```

`../tools/archive.py` - the held-out gain and the parent rule:

```python
            best = max(mine, key=lambda r: r["val_score"])["recipe"]
            base = max(control, key=lambda r: r["val_score"])["recipe"]
            gains[task["name"]] = round(tasks.score_on(task, a.seed, best, "private") - tasks.score_on(task, a.seed, base, "private"), 4)
```

```python
        best = max(index, key=lambda e: (e["held_out"] if e["held_out"] is not None else -1, -index.index(e)))
```

`../tools/patch_pack.py` - `approval: both`, the gate then the human:

```python
        if mode == "both":
            proposals.save(path, record)
            run.log("gate_kept", proposal=record["id"], version=label, gate=verdict)
            return {"id": record["id"], "decision": None, "gate": verdict, "landed": "pending", "version": label, "diff": diff,
```

The recorded run (Claude Code 2.1.278, headless, 27 turns + 3, 436 s + 39 s;
the benchmark's fit calls trimmed to the agent's notes):

```text
[Skill dgm-meta]
$ python ../tools/archive.py --pack .claude/skills/dgm-meta --task .claude/skills/dgm-meta/held-out/02_pool_trees_2.json --target .claude/skills/adult-income --action list
{"action": "list", "variants": [], ...}
agent> Empty archive. Step 1, held-out task 1, control arm: ... FREEZE. Best val: hgb,0.1,yes,ordinal,none = 0.9331.
agent> Control arm on task 1 done (val 0.9331, test 0.9093). Now the memory arm on task 1, seed 1. The pack's
policy is static, so read_memory --order static gives the next eight. No cards, policy static -> the memory
arm walks the static list too.
agent> My tally matches the script's (class_weight: balanced 10-2; encode 6-6 tie; model: hgb 16, rf 8-8,
logreg 0-16; scale: no 4-0; no hyper pairs, no errors). Writing the six cards in one call.
agent> Task 1 complete (verifier: 6 cards written, 6 new, 0 demoted). Now task 2, control arm: best val
hgb,0.1,yes,onehot,balanced = 0.8837. Now the memory arm on task 2. Three cards apply now, but the pack's
policy is still static, so the walk is unchanged by them.
agent> Step 1 done: both arms and the verifier on both tasks (verifier task 2: 8 cards, 2 new, 1 demoted -
scale=no was contradicted). Step 2, archive the current variant:
$ python ../tools/archive.py ... --action add --label gen1-static --held-out .claude/skills/dgm-meta/held-out --seed 1
{"action": "add", "label": "gen1-static", "variants": [{"label": "gen1-static", "problem": "pool_trees_2", "held_out": 0.0, "parent": null, "policy": "static"}]}
agent> Held-out score 0.0, as expected - a static memory arm walks exactly the control's path. Step 3, choose the parent:
$ python ../tools/archive.py ... --action parent
{"parent": "gen1-static", "held_out": 0.0, "latest": "gen1-static", "is_latest": true, "policies_in_archive": ["static"]}
agent> Parent gen1-static, is_latest true -> no restore needed. policies_in_archive = [static], so the rewrite
is obey-memory. Step 4: writing both files under runs/dgm-meta/patch/. Evidence recipe: the memory arm's best
val recipe on T was hgb,0.1,yes,onehot,balanced. Submitting the patch to the private gate:
$ python ../tools/patch_pack.py ... --files @runs/dgm-meta/patch --recipe model=hgb,hyper=0.1,scale=yes,encode=onehot,class_weight=balanced --summary "gen2: obey-memory from gen1-static" --visit 1
{"id": "g1", "decision": null, "gate": {"before": 0.8737, "after": 0.8737, "keep": true}, "landed": "pending", "version": "gen_001", "diff": "--- a/SKILL.md ... -   Search policy: static\n+   Search policy: obey-memory ... --- a/loop.json ... -  \"policy\": \"static\",\n+  \"policy\": \"obey-memory\", ...", "next": "The gate kept it. Show the diff to the user, ask approve / edit / reject ..."}
agent> The private gate kept the rewrite (proposal g1, before 0.8737 -> after 0.8737, keep: true). Per the
skill, I now need your verdict before it lands.
[27 turns, 436 s]
=== user> approve
$ python ../tools/patch_pack.py ... --proposal g1 --approved "approve"
{"id": "g1", "decision": "y", "landed": true, "version": "gen_001", "files": ["SKILL.md", "loop.json"], "approved_by": "human", "words": "approve"}
$ grep -n "Search policy:" .claude/skills/adult-income/SKILL.md && grep -n '"policy"' .claude/skills/adult-income/loop.json
26:   Search policy: obey-memory
6: "policy": "obey-memory",
agent> Generation 1 is complete. Landed: proposal g1 - approved_by: human, words "approve", version gen_001,
files SKILL.md + loop.json. Archive after this generation: gen1-static | static | held-out 0.0 | parent -.
The rewritten pack (obey-memory from gen1-static) is not in the archive yet - per the one-generation-deep rule
it enters only after it has run the benchmark. That's the next visit: generation 2 ... With three active cards
(model=hgb, class_weight=balanced, encode=ordinal), the memory arm should probe hgb first this time rather
than spending 16 fits on logreg and rf.
[3 turns, 39 s]
```

What to notice, honestly: generation 1's held-out score is 0.0 by
construction (a `static` memory arm walks the control's path), and the gate
kept the rewrite on a tie (0.8737 = 0.8737: the evidence recipe *is* the
incumbent on generation 1). The lesson's claim is not that the rewrite wins;
it is that the rewrite goes through an archive with a score, a parent rule
that ignores recency, a gate, and a human - and that `SKILL.md` and
`loop.json` are the only files it may touch. The test shows the parent rule
skipping a newer, worse variant and the gate rolling back a rewrite whose
evidence recipe scores lower.

Files:

```text
step_14_rsi_self_modifying/
├── README.md, test_step.py, .claude/settings.json
├── .claude/skills/adult-income/          + loop.json (policy field); the two self-modified files
├── .claude/skills/adult-income-verifier/
├── .claude/skills/dgm-meta/              SKILL.md (approval: both, patches: SKILL.md, loop.json), tools.md, held-out/{01,02}_pool_trees_*.json
├── .agents/skills/...
└── runs/adult-income/archive/            archive.json + one snapshot per variant   (after a run)
```

## Governance considerations

- **Who approves what.** The gate first (the private split of the last
  held-out task), then the human; the archive rule (best score, ties to the
  older), the benchmark and the one-generation-deep rule are the human's.
- **The hook.** Blocks the second `patch_pack.py` call without the user's
  words; the locked test.
- **What the script refuses.** A patch outside `SKILL.md` / `loop.json`; a
  rewrite the gate scores lower (rolled back, never archived); `archive add`
  without both arms on the benchmark; a fit or a test score for the meta pack.
- **What is and is not self-modified.** `SKILL.md` and `loop.json` are - the
  harness source. `schema.json`, `memory.json` (the verifier's), the
  verifier, the archive rule and the benchmark are not.

## How to measure it

| Claim | Test |
|---|---|
| the archive holds every variant with its held-out score; the parent is chosen by score, not recency (a newer, worse variant is skipped); restore works | `test_archive_holds_every_variant_and_the_parent_is_by_score_not_recency` |
| a rewrite whose evidence recipe scores lower on the private split is rolled back and never archived | `test_rewrite_that_lowers_the_private_score_is_rolled_back_and_never_archived` |
| only `SKILL.md` and `loop.json` change; the human comes after the gate and a "no" rolls back; the meta pack cannot score | `test_only_skill_and_loop_are_self_modified_and_the_human_comes_after_the_gate` |
| the held-out benchmark is disjoint from the curriculum and the exam | `test_held_out_is_disjoint_from_the_curriculum` |
| the pack contract | `test_pack_contract` |
| the recorded run reproduces (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 15 - AIDE²](../step_15_rsi_aide2/README.md). Previous:
[Lesson 13 - Recuris](../step_13_rsi_skill_memory/README.md).
