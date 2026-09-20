# Lesson 14 - The Darwin Gödel Machine lineage: the agent's own source, behind an archive and a gate

The Darwin Gödel Machine (arXiv:2505.22954) rewrites the agent's own code,
keeps an archive of every variant with its benchmark score, and picks the
next parent from the archive rather than always from the latest. Here the
agent's "source" is the actor's `SKILL.md` and `loop.json` - the policy line
and the `policy` field - and the meta pack `dgm-meta` runs one generation
per visit: score the current variant on a fixed held-out benchmark (two
seeded tables under `held-out/`, never a curriculum or exam problem), put it
in the archive, choose the parent (best held-out score, ties to the older
one), stand on it, propose one rewrite of the parent's two source files, and
send it through the gate and then the human (`approval: both`). A variant
that lowered the score stays in the archive with its score and is never
picked over a better one; a rewrite the gate rejected never runs and never
enters the archive. The paper's Challenge 2 verbatim: DGM's archive and
parent selection stayed human-fixed, and so do ours - the page says what is
and is not self-modified.

## Getting started

Prerequisites: lesson 09 (the gate, `propose`, `apply`). This lesson adds
`loop.json` to the actor (with a `policy` field the policy line must agree
with), `dgm-meta` with `held-out/` (two `intent.md` directories) and the
`archive` contract, `approval: both`, `patches: ["SKILL.md", "loop.json"]`.

## How to execute it

1. Open your agent in this directory and type the prompt:

   ```text
   Use the dgm-meta skill: run one generation - the held-out benchmark (both arms and the verifier on both tasks), archive the variant, choose the parent, propose one rewrite of the actor's SKILL.md and loop.json, put it through the gate, and ask me.
   ```

2. If the gate kept the rewrite, the agent shows the diff and asks
   **approve / edit / reject**. Answer `approve` (as recorded).

3. Headless, as recorded, two turns:

   ```bash
   claude -p "<the prompt above>" --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   claude -p --continue "approve" --allowedTools "Bash,Read,Write,Edit,Skill" --setting-sources project --strict-mcp-config
   ```

4. Tests: `python run_tests.py rsi`. Offline: the only self-modified files
   are `SKILL.md` and `loop.json`; the archive and parent rule are stated;
   the held-out seeds are disjoint and the human comes after the gate.
   `RSI_LIVE=1`: the archive holds the variant with `score.json`; both
   held-out tasks scored; a `gate` event; on `approve` the words in
   `.approved`, `loop.json`'s `policy` changed and the policy line agreeing;
   a version on disk.

5. To reset: `git checkout -- .claude .agents && rm -rf runs`.

## What it looks like

`.claude/skills/dgm-meta/SKILL.md` - the archive and the parent:

```markdown
3. Archive the variant with its held-out score: `archive M T --target P --action add --label gen<g>-<current policy> --held-out M/held-out --seed <g>`. The score is, over the held-out tasks, the private score of the memory arm's best recipe minus the control arm's, averaged: a gain over the static walk on a fixed benchmark.
4. Choose the parent: `archive M T --target P --action parent`. The parent is the variant with the best held-out score, ties to the older one; it is not the latest by default. If `is_latest` is false: `archive M T --target P --action restore --label <parent>`, then `read_pack P`; you now stand on the parent.
5. Propose ONE rewrite of the parent's source: the `Search policy:` line of `SKILL.md` and the `policy` field of `loop.json` set to the first of `static`, `obey-memory`, `neighbours-of-top-3`, `prefer-untried-family` that `policies_in_archive` does not hold (nothing to propose when all four are there: say so and stop). ...
6. `approval: both`: first `gate M T <id>` - the private split of `T` decides keep-or-rollback; if it kept the rewrite, show the user the diff and ask **approve / edit / reject**, wait, and land their answer: ...
```

`.claude/skills/adult-income/loop.json`:

```json
{
 "kind": "counted_while",
 "N": 24,
 "counter": "t",
 "error_still_counts": true,
 "policy": "static",
 "body": ["recipes = the next recipes of the Search policy (read_memory --order <policy>)", "fit_recipe(recipes)"],
 "exit": ["FREEZE", "score_test once", "scorecard"],
 "illegal": ["change N", "a second while", "score_test before FREEZE"]
}
```

`.claude/skills/dgm-meta/tools.md` - the archive contract:

```markdown
- `archive(pack, task, target, action, ...)` - `add --label <label> --held-out <dir> --seed <g>`: score the current variant of the target pack as, averaged over the held-out problems, the memory arm's best recipe's `private_score` minus the control arm's (a gain over the static walk on a fixed benchmark), copy the pack under `runs/<pack name>/archive/<label>/` with `score.json` (`label`, `score`, `policy`, `parent`, checksums) and print it. `parent`: the archived variant with the best score, ties to the older one - not the latest by default; print `label`, `score`, `is_latest`, `policies_in_archive`. `restore --label <label>`: write that variant's files over the target (both mirrors) after snapshotting it under `versions/`. A variant the gate rejected never runs and never enters the archive.
```

`test_step.py`:

```python
    assert procedure.index("`gate M T") < procedure.index("approve / edit / reject") < procedure.index("`apply M T")
```

The recorded run (Claude Code 2.1.278, headless, two turns; the arms
trimmed, the archive, the rewrite and the verdicts in full):

<!-- transcript -->

Files:

```text
step_14_rsi_self_modifying/
├── README.md
├── test_step.py
├── .claude/settings.json
├── .claude/skills/
│   ├── adult-income/                 SKILL.md (Search policy: static), loop.json (policy: static), memory.json, eval.md ...
│   ├── adult-income-verifier/
│   └── dgm-meta/                     SKILL.md, tools.md (archive, propose, gate, apply ...), config.md, held-out/{01_heldout_1, 02_heldout_2}/intent.md
├── .agents/skills/                   the same
└── runs/                             (after a run) adult-income/{heldout_1, heldout_2, versions/}, dgm-meta/{helpers/, archive/<label>/score.json, heldout_2/proposals/}
```

## Governance considerations

- **Who approves what.** The gate first (the private split of the last
  held-out task), then the human on the diff. The archive rule (best score,
  ties older), the one-generation-deep rule, the policy menu and the
  benchmark are human-fixed.
- **The hook.** `apply` only with an `.approved` file; the gate is not
  `apply`.
- **What the helper refuses.** `propose`: any file but the two source files;
  `archive`: a rewrite the gate rejected never enters; `private_score` for
  an actor.
- **What is and is not self-modified.** `SKILL.md` and `loop.json` of the
  actor - the harness source - and nothing else; the test asserts the
  `patches:` list. The meta pack, the verifier, the archive rule and the
  gate do not change.
- **Rung.** L5 flavour: the agent's own source, one generation at a time,
  behind a protected evaluator and a human.

## How to measure it

| Claim | Test |
|---|---|
| `SKILL.md` and `loop.json` are the only self-modified files; `approval: both`; `policy` agrees with the policy line | `test_source_files_are_the_only_self_modified_ones` |
| the archive scores on the held-out benchmark; the parent is the best, ties older, not the latest; a rejected rewrite never enters | `test_archive_and_parent_rule` |
| the held-out tables are disjoint (`role: pool`, seeds 201 / 202); the gate comes before the human, the human before `apply` | `test_held_out_is_disjoint_and_the_human_comes_after_the_gate` |
| the pack contract for three packs and the two held-out intents | `test_front_matter` .. `test_intent_contract` |
| the recorded run: the archive with a score, a gate event, `approve` landing the rewrite with `loop.json` and the policy line agreeing, a version (`RSI_LIVE=1`) | `test_live_claude_code` |

Run: `python run_tests.py rsi` from the repo root.

## Next lesson

[Lesson 15 - AIDE²](../step_15_rsi_aide2/README.md): keep-if-better across
the set under one budget. Previous: [lesson 13 - Recuris](../step_13_rsi_skill_memory/README.md).
