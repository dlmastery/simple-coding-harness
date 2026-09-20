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

```text
[Skill adult-income-curriculum]
[Read the five packs' SKILL.md and tools.md, eval.md, schema, memory schema, the two config.md]
agent> Now the pack tools.md files, schema, config, and what already exists under runs/.
$ ls -la && ls ../tasks && ... ls */runs/*/helpers 2>/dev/null ...
[Read ../step_07_proof/runs/adult-income/helpers/{rt.py, tools.py}, ../step_08_meta_generates_rsi/runs/rsi-writer/helpers/*.py]
agent> Now I'll build the helpers. Actor runtime first (trimmed to this lesson's two policies).
[Write runs/adult-income/helpers/rt.py]  [Write runs/adult-income/helpers/tools.py]
agent> Now the verifier's helper and the curriculum's.
[Write runs/adult-income-verifier/helpers/verify.py]  [Write runs/adult-income-curriculum/helpers/curriculum.py]  [Write runs/adult-income-meta-gate/helpers/meta.py]
agent> Helpers built. Problem 1 - control arm, then memory arm.
$ ... run_arm $P ../tasks/01_adult_income --arm control --memory off ...; grep -n "Search policy:" $P/SKILL.md; ... run_arm ... --arm memory ...
26:   Search policy: static
control policy static | best_val 0.9177 test 0.9049 fits 24 wasted 16
memory policy static applicable 0 | best_val 0.9177 test 0.9049 fits 24 wasted 16
agent> Both arms of problem 1 identical (static policy, no cards yet - as designed). Now the verifier: tally, then cards.
$ ... read_traces ... --scope problem --tally ...; ... write_card ... --as .claude/skills/adult-income-verifier --cards @runs/adult-income-verifier/cards_01.json
{"n": 9, "new": 9, "demoted": 5, "total_on_disk": 9, "active": 4}
$ ... meta.py read_traces $P $T --scope all ...; ... read_memory ...; ... read_pack ...
agent> Rule (a) applies: policy line is static and 4 cards are active. I write the patched SKILL.md (one line changed) under the meta pack's patch directory.
$ mkdir -p runs/adult-income-meta-gate/patch && python - <<'EOF'
src = open(".claude/skills/adult-income/SKILL.md", encoding="utf-8", newline="").read()
assert src.count("   Search policy: static\n") == 1
dst = src.replace("   Search policy: static\n", "   Search policy: obey-memory\n")
open("runs/adult-income-meta-gate/patch/SKILL.md", "w", encoding="utf-8", newline="").write(dst)
print("written; changed lines:", sum(1 for a, b in zip(src.splitlines(), dst.splitlines()) if a != b))
EOF
written; changed lines: 1
$ python $M propose $MP $T --target adult-income --files runs/adult-income-meta-gate/patch --recipe '{"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}' --summary "flip Search policy static -> obey-memory: 4 cards active after problem 1 (rule a)" --visit 1
{"id": "p001", "visit": 1, "target": "adult-income", "summary": "flip Search policy static -> obey-memory: 4 cards active after problem 1 (rule a)", "recipe": {...}, "changed_lines": 1, "cap": "ok", "lint": "ok", ...}
$ python $M gate $MP $T p001; grep -n "Search policy:" .claude/skills/adult-income/SKILL.md .agents/skills/adult-income/SKILL.md; diff -r .claude/skills .agents/skills && echo MIRRORS_EQUAL
{"decision": "keep", "id": "p001", "summary": "...", "before": 0.8977, "after": 0.8977, "keep": true, "landed": true, "version": "gen_001", ...}
.claude/skills/adult-income/SKILL.md:26:   Search policy: obey-memory
.agents/skills/adult-income/SKILL.md:26:   Search policy: obey-memory
MIRRORS_EQUAL
$ ... problem 2 (02_breast_cancer): grep -n "Search policy:" $P/SKILL.md | head -1; run_arm control; run_arm memory
26:   Search policy: obey-memory
control policy static applicable 0 | best_val 0.9954 test 0.9806 fits 24 wasted 0 best {'model': 'hgb', 'hyper': 0.1, ...}
memory policy obey-memory applicable 1 preferred {'scale': 'yes'} | best_val 0.996 test 0.9841 fits 24 wasted 0 best {'model': 'hgb', 'hyper': 0.3, ...}
$ ... verifier on problem 2 (54 pairs; cards_by_rule: n_rows < 1000 -> prefer hgb, ...) ...
agent> Meta visit 2: read the log, cards, pack, then apply the rule.
$ python $M read_traces $P $T --scope all --tally | ... (rule b candidates: lost >= 3, never won, not hyper)
rows(all) 48 pairs 178
wins   {"class_weight": {"none": 21, "balanced": 8}, "encode": {"onehot": 18, "ordinal": 4}, ...}
losses {"class_weight": {"balanced": 21, "none": 8}, "encode": {"ordinal": 18, "onehot": 4}, ...}
rule b candidates (lost >=3, never won, not hyper): []
[Edit runs/adult-income-meta-gate/helpers/meta.py]  (rule b tallied within each problem, then summed: a pair across two tables means nothing)
rule b candidates: [('encode', 'ordinal', 12)]
$ ... propose p002 (schema.json -> forbid [{"field": "encode", "value": "ordinal"}]) --visit 2; gate p002
{"decision": "keep", "id": "p002", "before": 1.0, "after": 1.0, "landed": true, "version": "gen_002"}
$ ... problem 3 (wine), both arms, verifier, meta visit 3 ...
rule b candidates: []   rule c: cards_by_rule not held by memory: []   cards 19 active 9
agent> Visit 3: nothing applies. (logged) ... problem 4 (digits) ...
agent> Visit 4: nothing applies. Logging it, then problem 5.
$ mkdir -p runs/adult-income-meta-gate/digits && echo '{"event": "visit", "visit": 4, "problem": "digits", "proposed": false, "why": "rule a: policy already obey-memory; rule b: no unforbidden value lost >=3 and never won; rule c: every card_by_rule is already held"}' >> runs/adult-income-meta-gate/digits/traces.jsonl; ... run_arm ... 05_synth_shift_a ...
control policy static | best_val 0.9378 test 0.8981 fits 24 wasted 8 best {'model': 'rf', 'hyper': 16, ...}
memory policy obey-memory applicable 4 preferred {'hyper': 0.1, 'class_weight': 'none'} forbidden {'encode': ['ordinal']} | best_val 0.9378 wasted 1
... problem 6 ... visit 6: nothing to propose ...
agent> Visit 6: nothing to propose. Now the learning curve.
$ python runs/adult-income-curriculum/helpers/curriculum.py curve .claude/skills/adult-income --tasks ../tasks | ...
problem       | policy      | memory_best_val | control_best_val | gap_val | wasted_memory | wasted_control | cards_added | cards_demoted | cards_active
adult_income  | static      | 0.9177          | 0.9177           | 0.0     | 16            | 16             | 9           | 5             | 4
breast_cancer | obey-memory | 0.996           | 0.9954           | 0.0006  | 0             | 0              | 6           | 8             | 7
wine          | obey-memory | 1.0             | 1.0              | 0.0     | 0             | 0              | 1           | 8             | 8
digits        | obey-memory | 0.999           | 0.999            | 0.0     | 0             | 0              | 3           | 10            | 9
synth_shift_a | obey-memory | 0.9378          | 0.9378           | 0.0     | 1             | 8              | 5           | 14            | 10
synth_shift_b | obey-memory | 0.7685          | 0.7685           | 0.0     | 4             | 9              | 1           | 16            | 9
$ ... sha256sum $P/memory.json; grep -n "Search policy:" $P/SKILL.md | head -1; for s in 0 1 2 3 4; do run_arm control --seed $s --memory off; run_arm memory --seed $s; done
c5ddb70d57d97e56fd1ced5c32e03b1520972fb461a2607fd55e5c838a8261d4
26:   Search policy: obey-memory
seed 0 control policy static      applicable 0 best_val 0.9389 test 0.7831 wasted 8  best {"model": "rf", "hyper": 16, ...}
seed 0 memory  policy obey-memory applicable 4 best_val 0.9412 test 0.7819 wasted 1  best {"model": "rf", "hyper": null, ...}
seed 1 control policy static      applicable 0 best_val 0.8615 test 0.7244 wasted 17 best {"model": "hgb", "hyper": 0.1, ..., "class_weight": "balanced"}
seed 1 memory  policy obey-memory applicable 4 best_val 0.872  test 0.717  wasted 7  best {"model": "hgb", "hyper": 0.3, ..., "class_weight": "none"}
... (6 more arms)
$ python runs/adult-income-curriculum/helpers/curriculum.py exam .claude/skills/adult-income ../tasks/07_exam --seeds 0,1,2,3,4 | ...; sha256sum .claude/skills/adult-income/memory.json .agents/skills/adult-income/memory.json | cut -c1-16; ls runs/adult-income/curve.json runs/adult-income/exam.json
seed | memory_test | control_test | memory_wasted | control_wasted | winner  | applicable_cards | not_transferred
0    | 0.7819      | 0.7831       | 1             | 8              | control | 4                | 2
1    | 0.717       | 0.7244       | 7             | 17             | control | 4                | 2
2    | 0.8288      | 0.8288       | 1             | 8              | memory  | 4                | 1
3    | 0.8335      | 0.8335       | 1             | 8              | memory  | 4                | 1
4    | 0.8333      | 0.8178       | 7             | 16             | memory  | 4                | 2
wins 3 of 5 | mean_test_gap 0.0014 | pack_unchanged True | no_card_written True
sha before c5ddb70d...   sha after  c5ddb70d...
agent> Finally, the versions on disk and a mirror check.
$ ... read_pack .claude/skills/adult-income --checksums ...; diff -r .claude/skills .agents/skills && echo MIRRORS_EQUAL; cat runs/adult-income-meta-gate/*/traces.jsonl | ...
policy_line obey-memory | mirrors_equal True
versions:
  gen_001 | visit 1 adult_income | p001 keep | before 0.8977 after 0.8977 | snapshot policy static -> after obey-memory
  gen_002 | visit 2 breast_cancer | p002 keep | before 1.0 after 1.0 | snapshot policy obey-memory -> forbid [encode=ordinal]
MIRRORS_EQUAL
{'event': 'propose', 'id': 'p001', 'visit': 1} {'event': 'gate', 'id': 'p001', 'keep': True, 'before': 0.8977, 'after': 0.8977, 'version': 'gen_001'} {'event': 'propose', 'id': 'p002', 'visit': 2} {'event': 'gate', 'id': 'p002', 'keep': True, 'before': 1.0, 'after': 1.0, 'version': 'gen_002'} {'event': 'visit', 'visit': 3, 'proposed': False} ... {'event': 'visit', 'visit': 6, 'proposed': False}
agent> Done. Helpers were built from the contracts (actor runs/adult-income/helpers/, verifier, curriculum, meta-gate), then the curriculum, the curve, the exam and the version list ran as the skill specifies. curve.json and exam.json are under runs/adult-income/, both mirrors are byte-identical, and every arm was frozen and test-scored exactly once (test_touched_before_freeze: false everywhere).
Problem 1 ran static on both arms (the actor ships static; no card yet), so its two arms are identical by construction. From problem 2 on the memory arm booted the policy line gen_001 wrote.
## Meta decisions (gate, nobody asked)
| adult_income   | 1 | p001 - Search policy: static -> obey-memory (rule a: 4 cards active)                                     | keep, landed | 0.8977 -> 0.8977 | gen_001 |
| breast_cancer  | 2 | p002 - schema.json forbid {encode: ordinal} (rule b: lost all 12 one-field comparisons, never won)        | keep, landed | 1.0 -> 1.0       | gen_002 |
| wine, digits, synth_shift_a, synth_shift_b | 3-6 | nothing proposed (a: already obey-memory; b: no candidate; c: every card by rule already held) | - | - | - |
read_pack P --checksums: two versions on disk, gen_001 (snapshot: policy static) and gen_002 (snapshot: obey-memory, no forbid list); the booting pack has Search policy: obey-memory, forbid [encode=ordinal], 25 cards (9 active), mirrors equal. Note the gate scored the evidence recipe against an incumbent that was the same recipe (best of the newest problem in the log), so both gates were after == before keeps - a sanity gate, not a discriminating one. Rule (b) was computed with pairs tallied within each problem and summed over the log (a pair across two tables means nothing).
## The claims of eval.md
- gap_val never negative - held: 0.0, 0.0006, 0.0, 0.0, 0.0, 0.0.
- gap larger on problem 6 than on problem 2 - did not hold: gap_6 = 0.0 vs gap_2 = 0.0006; wine, digits and the synthetic tables saturate this recipe space, and 0 is the honest number (the memory arm did reach the control's best with fewer wasted fits on problems 5 and 6: 1 vs 8, 4 vs 9).
- exam: memory wins >= 3 of 5 - held, exactly 3 of 5 (two on equal test score with fewer wasted fits, one on a higher test score; seeds 0 and 1 went to control by 0.0012 and 0.0074).
- memory.json byte-identical across the exam - held. The report names every applicable card that did not transfer - held (the two hyper cards). Test split scored once per arm, after FREEZE - held on all 22 arms.
[62 turns, 1208 s]
```

What to notice under the gate: two patches in six visits, both by the rule
- the policy flip after problem 1 (rule a) and a `forbid` of
`encode: ordinal` after problem 2 (rule b: lost all twelve one-field
comparisons, never won) - and four visits that proposed nothing and said
why. Generation 2 booted what generation 1 wrote: the curve's `policy`
column shows `static` on problem 1 and `obey-memory` from then on, which is
the recursion. The agent also noticed something about its own gate: the
evidence recipe was the incumbent, so `before == after` and every keep was
a sanity check rather than a discriminating one; the page keeps that
sentence. The exam held at exactly 3 of 5 with the same two `hyper` cards
not transferring as in lesson 07.

The recorded human visit (two turns; the arms trimmed):

```text
[Skill adult-income-curriculum]
[Read the actor's, verifier's and meta's SKILL.md and tools.md, eval.md, schema, memory schema, config, memory.json]
$ ls -la && ls ../tasks && cat ../tasks/01_adult_income/intent.md && ... python -c "import sklearn, pandas, numpy; print(...)"
$ cd /c/Users/evija/simple-coding-harness/rsi && ls */runs/*/helpers 2>/dev/null | head -50; ...
[Read ../step_07_proof/runs/adult-income/helpers/{rt.py, tools.py}, .../verify.py, .../curriculum.py, ../step_08_meta_generates_rsi/runs/rsi-writer/helpers/*.py]
agent> Now the actor's tools.
[Write runs/adult-income/helpers/rt.py]  [Write runs/adult-income/helpers/tools.py]
agent> Now the verifier's helpers.
[Write runs/adult-income-verifier/helpers/verify.py]
agent> Now the meta pack's helpers (with the lint and a decide view of the a/b/c rule).
[Write runs/adult-income-meta/helpers/meta.py]
agent> Now the curriculum's helpers (curve, exam, read_pack).
[Write runs/adult-income-curriculum/helpers/curriculum.py]
agent> Helpers built. Now problem 1, step 2a - the control arm (--arm control --memory off, the static list in one call, test scored once after FREEZE, scorecard):
$ python runs/adult-income/helpers/tools.py run_arm .claude/skills/adult-income ../tasks/01_adult_income --arm control --memory off
{... "scorecard": {"best_val_score": 0.9177, "test_score": 0.9049, "fits_used": 24, "wasted_fits": 16, ...}}
$ grep -n "Search policy:" .claude/skills/adult-income/SKILL.md && ...
26:   Search policy: static
agent> The policy line still says static (nothing has patched it yet). Memory arm, following it - read_memory --order static for the next recipes, fit until FREEZE, score once, scorecard:
$ python runs/adult-income/helpers/tools.py run_arm .claude/skills/adult-income ../tasks/01_adult_income --arm memory --order static | ...
{"arm": "memory", "seed": 0, "problem": "adult_income", "memory": "on", "search_policy": "static", "applicable_cards": [], "preferred": {...null...}, ... "scorecard": {"best_val_score": 0.9177, "test_score": 0.9049, "wasted_fits": 16, ...}}
$ python runs/adult-income-verifier/helpers/verify.py read_traces .claude/skills/adult-income ../tasks/01_adult_income --scope problem --tally | ...
{"profile": {"n_rows": 6000, "n_features": 14, "n_classes": 2, "imbalance": 0.239, "has_categorical": 1}, "n_rows": 24, "n_pairs": 60, "wins": {...}, "losses": {...}, "errored": {}, "cards_by_rule": [... 9 cards ...]}
$ ... write_card .claude/skills/adult-income ../tasks/01_adult_income --as .claude/skills/adult-income-verifier --cards @runs/adult-income-verifier/cards_01.json && diff .claude/skills/adult-income/memory.json .agents/skills/adult-income/memory.json && echo "mirrors identical"
{"n": 9, "new": 9, "demoted": 5, "total_on_disk": 9, "active": 4}
mirrors identical
$ python runs/adult-income-meta/helpers/meta.py read_traces .claude/skills/adult-income ../tasks/01_adult_income --scope all | ... && ... read_memory ... && ... read_pack .claude/skills/adult-income && ... decide .claude/skills/adult-income-meta ../tasks/01_adult_income --target adult-income | ...
{"scope": "all", "n_rows": 24, "problems": {"adult_income": 24}, "profile": {...}}
{"memory": "on", "n_cards": 9, "active": 4, "demoted": 5, "preferred": {"model": "hgb", "hyper": null, "scale": "yes", "encode": "onehot", "class_weight": "none"}, "forbidden": {...}}
{"rule": "a", "reason": "Search policy: static and 4 active cards", ...}
agent> Rule a applies: the policy line says static and 4 cards are active. Checking the file's line endings before I write the patched SKILL.md (a CRLF/LF mismatch would blow the 20 % cap):
$ file .claude/skills/adult-income/SKILL.md && python -c "..."
.claude/skills/adult-income/SKILL.md: ASCII text, with very long lines (742)
LF 4107 trailing newline: True
[Write runs/adult-income-meta/patch/SKILL.md (43 lines)]
agent> Now propose, with the evidence recipe (the best val recipe of problem 1) and a one-line summary:
$ python runs/adult-income-meta/helpers/meta.py propose .claude/skills/adult-income-meta ../tasks/01_adult_income --target adult-income --files runs/adult-income-meta/patch --recipe '{"model": "hgb", "hyper": 0.1, "scale": "yes", "encode": "onehot", "class_weight": "none"}' --summary "Flip the actor's Search policy line from static to obey-memory: after problem 1 the verifier left 4 active cards (prefer hgb, scale yes, onehot, class_weight none), so rule (a) applies" --visit 1
{"id": "p001", "visit": 1, "target": "adult-income", "files": ["SKILL.md"], "changed_lines": 2, "pack_lines": 588, "cap": "ok", "lint": "ok", "diff": "..."}
agent> Problem 1 is done through the verifier, and the meta pack has proposed its patch. Nothing has landed - no gen_NNN version exists, both mirrors are untouched, and I'm stopping here for your decision.
## Problem 1 - adult_income (6,000 rows, 14 features, 2 classes, imbalance 0.239, categorical)
| arm                    | policy                    | fits | best val | best recipe                            | test (once, after FREEZE) | wasted |
| control (--memory off) | static                    | 24   | 0.9177   | hgb / 0.1 / scale yes / onehot / none  | 0.9049                    | 16 |
| memory                 | static (the shipped line) | 24   | 0.9177   | same                                   | 0.9049                    | 16 |
gap_val = 0 - expected: the pack shipped with Search policy: static and an empty memory.json, so the memory arm had no cards to obey.
Verifier (60 one-field-apart pairs): 9 cards written, 9 new, 5 demoted (the counter cards), 4 active - on this profile prefer model: hgb, scale: yes, encode: onehot, class_weight: none. No errored fit, so no forbid card.
## Meta visit 1 - proposal p001 (rule a)
Search policy: says static and 4 cards are active -> flip the one line. Lint ok, 2 of 588 pack lines changed (cap 20 %), the test rule intact, evidence recipe = problem 1's best (hgb / 0.1 / yes / onehot / none).
--- a/adult-income/SKILL.md
+++ b/adult-income/SKILL.md
@@ -23,7 +23,7 @@
 3. Search, until a result says `FREEZE`, under the policy the line below names - the one line of this file a meta pack may patch:
-   Search policy: static
+   Search policy: obey-memory
    - `static`: walk `schema.json -> recipes` in order, in one call, cards or no cards.
approve / edit / reject? On approve I'll write your exact words to runs/adult-income-meta/adult_income/proposals/p001.approved, snapshot the actor as gen_001, and land the line in both mirrors. On edit: ... I'll put your version under proposals/p001-edited/ and apply that. On reject nothing lands.
[44 turns, 710 s]

--- turn 2: claude -p --continue "approve"
[Write runs/adult-income-meta/adult_income/proposals/p001.approved (1 lines)]
$ python runs/adult-income-meta/helpers/meta.py apply .claude/skills/adult-income-meta ../tasks/01_adult_income p001 --approved "approve"
{"id": "p001", "decision": "approved", "approved": "approve", "version": "gen_001", "files": ["SKILL.md"], "landed": true, "snapshot": "runs\\adult-income\\versions\\gen_001"}
$ grep -n "Search policy:" .claude/skills/adult-income/SKILL.md .agents/skills/adult-income/SKILL.md runs/adult-income/versions/gen_001/SKILL.md && diff -r .claude/skills .agents/skills && echo "mirrors identical" && cat runs/adult-income-meta/adult_income/traces.jsonl && ... read_pack ... --checksums ...
.claude/skills/adult-income/SKILL.md:26:   Search policy: obey-memory
.agents/skills/adult-income/SKILL.md:26:   Search policy: obey-memory
runs/adult-income/versions/gen_001/SKILL.md:26:   Search policy: static
mirrors identical
{"event": "propose", "id": "p001", "visit": 1, "target": "adult-income", "files": ["SKILL.md"], "summary": "Flip the actor's Search policy line from static to obey-memory: ...", "recipe": {...}}
{"event": "apply", "id": "p001", "approved": "approve", "version": "gen_001", "files": ["SKILL.md"]}
agent> Landed.
| proposal | decision | version | files changed |
| p001 - flip Search policy: static -> obey-memory (rule a: 4 active cards) | approve (your word, verbatim, in proposals/p001.approved and the apply trace event) | gen_001 | SKILL.md |
- runs/adult-income/versions/gen_001/ holds the pre-patch actor (its SKILL.md still says static) - rollback adult-income gen_001 undoes this.
- The live pack now reads Search policy: obey-memory in both mirrors (diff -r clean). Meta trace: propose then apply with "approved": "approve".
Per your request I stopped after problem 1, so curve.json / exam.json were not produced. The next generation is ready: when problem 2 boots, the memory arm re-reads P/SKILL.md and will follow obey-memory with the cards from problem 1. Say the word and I'll continue with problems 2-6, the curve, and the exam.
[4 turns, 50 s]
```

What to notice in the human visit: the meta pack's own `decide` named
rule (a) and the reason; the proposal was a two-line diff of one file out
of 588 pack lines, shown to the human with the cap and the evidence recipe;
nothing landed until `approve`; and the snapshot under `gen_001` still says
`static` while both mirrors say `obey-memory` - the version history is the
undo. The agent stopped exactly where the skill says to stop.

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
